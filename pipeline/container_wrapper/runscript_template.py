import json
import os
import logging
from subprocess import call
import traceback

import boto3.session
import botocore.exceptions

# user specified environment variable
UPLOADBUCKET = os.getenv('UPLOADBUCKET')
QUEUEURL = os.getenv('QUEUEURL')
REGION = os.getenv('REGION')

# get input/output file location
INPUT_PATH = %(input)s
OUTPUT_PATH = %(output)s

logger = logging.getLogger()
log_lvl = os.getenv('LOG_LVL', default='WARNING')

if log_lvl == 'ERROR':
    logger.setLevel(logging.ERROR)
elif log_lvl == 'INFO':
    logger.setLevel(logging.INFO)
elif log_lvl == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


def pull_files(message_URL):
    '''
    pull message form message_URL
    '''
    session = boto3.session.Session(region_name=REGION)
    s3 = session.client('s3')
    sqs = session.client('sqs')
    msgs = {}
    while 'Messages' not in msgs:
        logger.debug('pull message from SQS: %s', message_URL)
        try:
            msgs = sqs.receive_message(QueueUrl=message_URL)
        except botocore.exceptions.ClientError as err:
            logger.debug(traceback.format_exc())
            logger.warn(err.response)
        except Exception as err:
            logger.debug(traceback.format_exc())
            logger.error('Unexpected error occures at pull_files()!!')
            logger.error(err)

    logger.info('receive file info from SQS')
    for msg in msgs['Messages']:
        record = json.loads(msg['Body'])['Records'][0]
        bucket = record['s3']['bucket']['name']
        file = record['s3']['object']['key']
