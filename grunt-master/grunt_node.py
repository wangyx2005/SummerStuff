import json
import subprocess
import os
import logging
from time import wait
from queue import Queue

import requests
import requests.exceptions
from boto3 import client
import boto3.exceptions

from nodeconfig import *

'''
UPLOADBUCKET

'''

'''
for information about grunt, see https://github.com/Mayo-QIN/grunt
'''

logger = logging.getLogger(__name__)

JOB_DICT = \
    {
        'ip': '',
        'job_id': '',
        'source_file_name': '',
        'result_file_name': '',
        'source_file_path': '',
        'result_file_path': '',
        'resource_name': ''
    }

RESOURCE_DICT = \
    {
        'ip': '',
        'name': ''
    }


def pull_files(message_URL, future_job, wait_time=30, region='us-east-1'):
    s3 = client('s3', region)
    sqs = client('sqs', region)
    msgs = {}

    while True:
        while 'Messages' not in msgs:
            logger.debug('pull message from SQS: %s', message_URL)
            try:
                msgs = sqs.receive_message(QueueUrl=message_URL)
            except boto3.exceptions.ClientError as err:
                logger.debug(traceback.format_exc())
                logger.warn(err.response)
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error('Unexpected error occures!!')
                logger.error(err)
            wait(wait_time)

        logger.info('receive file info from SQS')
        for msg in msgs['Messages']:
            record = json.loads(msg['Body'])['Records'][0]
            bucket = record['s3']['bucket']['name']
            file = record['s3']['object']['key']
            job = dict(JOB_DICT)
            # just parse the real file name
            job['source_file_name'] = file.split('/')[-1]
            job['source_file_path'] = 'source/' + job['source_file_name']

            try:
                s3.download_file(bucket, file, 'source/' + file)
            except Exception as err:
                # put the failed file info back to sqs
                logger.warn(err)
                logger.debug(traceback.format_exc())
                logger.debug('message content: %s', json.dumps(record))
                logger.info('put message back to SQS for later try')
                try:
                    sqs.send_message(QueueUrl=message_URL,
                                     MessageBody=json.dumps(record))
                except Exception as err:
                    logger.warn(err)
                    logger.debug(traceback.format_exc())
                continue

            # put job into future_job queue
            logger.info('download file %s from S3 bucket', file)
            for service_name, job_queue in future_job:
                job_queue.put(dict(job))


def submit_processing(future_job, resource, working_job, wait_time=30):
    # service['ip'] already contains 'http://'
    while True:
        for service_name in resource.keys():
            if future_job[service_name].empty() \
                    or resource[service_name].empty():
                continue
            service = resource[service_name].get()
            job = future_job[service_name].get()
            result_file_name = 'Result-' + service_name + \
                '-' + job['source_file_name']
            # submit job to process
            try:
                para = {'output': result_file_name}
                file = {'input': open(job['source_file_path'], 'rb')}
                response = requests.post(
                    service['ip'] + '/rest/service/run_job', files=file, data=para)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                # TODO: add failed numbers for checking resource health
                # if cannot connect to service, put back for later use
                logger.warn('Cannot submit job %s on service %s at %s', (job[
                            'source_file_name'], service_name, service['ip']))
                logger.warn(err)
                source[service_name].put(service)
                future_job[service_name].put(job)
                continue
            except FileNotFoundError as err:
                logger.warn('Cannot find source file: %s',
                            job['source_file_path'])
                source[service_name].put(service)
                future_job[service_name].put(job)
                continue
            except Exception as err:
                logger.error('Unexpect error occurs on processing job %s on service %s at %s', (job[
                             'source_file_name'], service_name, service['ip']))
                logger.error(err)
                continue

            # put successful job into working job
            job['job_id'] = response.json()['uuid']
            job['ip'] = service['ip']
            job['result_file_name'] = result_file_name
            job['resource_name'] = service['name']
            working_job.put(job)
        # wait after each round is finished
        wait(wait_time)


def check_status(working_job, finished_job, resource):
    while True:
        for job in working_job:
            try:
                status = requests.get(job['ip'] + '/rest/job/' + job['job_id'])
                status.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.warn(err)
                working_job.put(job)
            except Exception as err:
                logger.error('Unexpected error occurs on check_status')