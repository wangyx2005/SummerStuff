import json
import subprocess
import os
import logging
from time import wait

import requests
from queue import Queue
from boto3 import client

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
    'result_file_path': ''
}


def pull_file(message_URL, future_job, wait_time=10, region='us-east-1'):
    s3 = client('s3', region)
    sqs = client('sqs', region)
    try:
        msgs = sqs.receive_message(QueueUrl=message_URL)
    except Exception as err:
        logger.debug(traceback.format_exc())
        logger.error(err)

    while True:
        while 'Messages' not in msgs:
            logger.debug('No message in current SQS: %s', message_URL)
            try:
                msgs = sqs.receive_message(QueueUrl=message_URL)
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error(err)
            wait(wait_time)

        logger.info('receive file info from SQS')
        for msg in msgs['Messages']:
            record = json.loads(msg['Body'])['Records'][0]
            bucket = record['s3']['bucket']['name']
            file = record['s3']['object']['key']
            job = dict(JOB_DICT)
            job['source_file_name'] = file
            job['source_file_path'] = 'source/' + file

            try:
                s3.download_file(bucket, file, 'source/' + file)
            except Exception as err:
                # put the failed file info back to sqs
                logger.error(err)
                logger.debug(traceback.format_exc())
                logger.debug('message content: %s', json.dumps(record))
                logger.info('put message back to SQS for later try')
                sqs.send_message(QueueUrl=message_URL,MessageBody=json.dumps(record))
            else:
                # put job into future_job queue
                logger.info('download file %s from S3 bucket', file)
                for service_name, job_queue in future_job:
                    job_queue.put(dict(job))


def submit_processing(future_job, resource, working_job):
    