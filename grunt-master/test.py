import json
import subprocess
import os
'''
This is a non-while-true version of grunt_node.py for testing purpose
'''

import logging
from time import sleep
from queue import Queue

import requests
import requests.exceptions
from boto3 import client
import boto3.exceptions

from nodeconfig import *

future_job = {'test': Queue()}
resource = {{'ip': 'http://192.168.'}}

logger = logging.getLogger(__name__)


def pull_files(message_URL, future_job, wait_time=30, region='us-east-1'):
    s3 = client('s3', region)
    sqs = client('sqs', region)
    msgs = {}

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
        sleep(wait_time)

    logger.info('receive file info from SQS')
    for msg in msgs['Messages']:
        record = json.loads(msg['Body'])['Records'][0]
        bucket = record['s3']['bucket']['name']
        file = record['s3']['object']['key']
        job = dict(JOB_DICT)
        # just parse the real file name
        job['source_file_name'] = file.split('/')[-1]
        job['source_file_path'] = 'source/' + job['source_file_name']
        job['bucket'] = bucket

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
                service['ip'] + '/rest/service/change', files=file, data=para)
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
        job['result_file_path'] = 'result/' + result_file_name
        job['resource_name'] = service['name']
        working_job.put(job)
    # wait after each round is finished
    sleep(wait_time)


def check_status(working_job, finished_job, resource, future_job, wait_time=180):
    for job in working_job:
        # check status
        try:
            status = requests.get(job['ip'] + '/rest/job/' + job['job_id'])
            status.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.warn(err)
            working_job.put(job)
            continue
        except Exception as err:
            logger.error('Unexpected error occurs on check_status')
            continue
        size = working_job.qsize()
        if status.json()['status'] is 'success':
            finished_job.put(job)
            service['name'] = job['service_name']
            service['ip'] = job['ip']
            resource[service['name']].put(service)
        # TODO: check the running status
        elif status.json()['status'] is 'run':
            working_job.put(job)
        # restart the job
        else:
            future_job.put(job)
            service['name'] = job['service_name']
            service['ip'] = job['ip']
            resource[service['name']].put(service)

        sleep(wait_time / size)


def upload_result(finished_job, result_bucket, region='us-east-1', stream_size=32):
    s3 = client('s3', region)
    job = finished_job.get()
    url = job['ip'] + '/rest/job/' + job['job_id'] + '/file/output'
    try:
        result = requests.get(url, stream=True)
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logger.warn(err)
        finished_job.put(job)
    except Exception as err:
        logger.error('Unexpeced error happend in retrieve file %s from %s',
                     (job['result_file_name'], job['ip']))
        logger.error(err)
    # save result at local
    with open(job['result_file_path', 'wb']) as f:
        for chunk in result.iter_content(chunk_size=stream_size):
            if chunk:  # filter out keep-alive new chunks
                f.write(chuck)
    logger.info('retrieve file %s', job['result_file_name'])

    # upload file to s3 bucket
    try:
        s3.upload_file(job['result_file_name'],
                       result_bucket, job['result_file_path'])
    except boto3.exceptions.ClientError as err:
        logger.warn(err)
        finished_job.put(job)
    except Exception as err:
        logger.debug(traceback.format_exc())
        logger.error('Unexpected error happend will upload file')
        logger.err(err)
    logger.info('upload file %s to s3 bucket %s',
                (job['result_file_name'], result_bucket))

    os.remove(job['result_file_path'])
    logger.info('remove file %s', job['result_file_name'])