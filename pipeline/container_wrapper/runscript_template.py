import json
import os
import logging
from subprocess import call
import traceback

import boto3.session
import botocore.exceptions

# TODO: need to check folder

# user specified environment variable
UPLOADBUCKET = os.getenv('output_s3_name')
QUEUEURL = os.getenv('sqs')
REGION = os.getenv('AWS_DEFAULT_REGION')
NAME = os.getenv('NAME', default='%(name)s')

# user define if want to zip the result file
# NEED_ZIP = os.getenv('ZIP', default='True')

# get input/output file location
INPUT_PATH = '%(input)s'
OUTPUT_PATH = '%(output)s'


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

logger.addHandler(logging.StreamHandler())


session = boto3.session.Session(region_name=REGION)
sqs = session.client('sqs')
s3 = session.client('s3')


def pull_files(message_URL):
    '''
    pull message form message_URL
    '''
    msgs = {}
    while 'Messages' not in msgs:
        logger.debug('pull message from SQS: {}'.format(message_URL))
        while 'Messages' not in msgs:
            try:
                msgs = sqs.receive_message(QueueUrl=message_URL)
            except botocore.exceptions.ClientError as err:
                logger.debug(traceback.format_exc())
                logger.warn(err.response)
                continue
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error('Unexpected error occures at pull_files()!!')
                logger.error(err)
                continue

        if '\"Records\"' not in msgs['Messages'][0]['Body']:
            # delete such message
            try:
                sqs.delete_message(QueueUrl=message_URL,
                                   ReceiptHandle=msgs['Messages'][0]['ReceiptHandle'])
            except botocore.exceptions.ClientError as err:
                logger.debug(traceback.format_exc())
                logger.warn(err.response)
                sqs.delete_message(QueueUrl=message_URL,
                                   ReceiptHandle=msgs['Messages'][0]['ReceiptHandle'])
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error('Unexpected error occures when delete message!!')
                logger.error(err)
            logger.info('delete one useless message from file queue')
            msgs = {}
        
    logger.info('receive file info from SQS')
    for msg in msgs['Messages']:
        record = json.loads(msg['Body'])['Records'][0]
        bucket = record['s3']['bucket']['name']
        file = record['s3']['object']['key']

        # delete message
        try:
            sqs.delete_message(QueueUrl=message_URL,
                               ReceiptHandle=msg['ReceiptHandle'])
        except botocore.exceptions.ClientError as err:
            logger.debug(traceback.format_exc())
            logger.warn(err.response)
            sqs.delete_message(QueueUrl=message_URL,
                               ReceiptHandle=msg['ReceiptHandle'])
        except Exception as err:
            logger.debug(traceback.format_exc())
            logger.error('Unexpected error occures when delete message!!')
            logger.error(err)
        logger.info('delete one message from file queue')

        # download file from input S3 bucket
        input_file = download_file(bucket, file, msg)
        if input_file == '':
            continue

        # run program
        result = run_program(input_file)

        # upload file
        upload_file(result, file)


def download_file(bucket, file, msg):
    file_name = file.split('/')[-1]
    try:
        s3.download_file(bucket, file, INPUT_PATH + file_name)
        logger.info('donwloaded file')
        return INPUT_PATH + file_name
    except Exception as err:
        # This part has problem. formate is wrong
        # put the failed file info back to sqs
        logger.warn(err)
        logger.debug(traceback.format_exc())
        logger.debug('message content: {}'.format(json.dumps(msg)))
        logger.info('put message back to SQS for later try')
        try:
            sqs.send_message(QueueUrl=message_URL,
                             MessageBody=json.dumps(msg))
        except Exception as err:
            logger.warn(err)
            logger.debug(traceback.format_exc())
            return ''
        return ''


def run_program(input_file):
    command = '%(command)s'

    file_name = input_file.split('/')[-1]
    result_file = OUTPUT_PATH + 'Result-' + NAME + '-' + file_name

    run_command = command.split()
    for i in range(len(run_command)):
        if run_command[i] == '$input':
            run_command[i] = input_file
        if run_command[i] == '$output':
            run_command[i] = result_file

    # with open(input_file, 'r') as f:
    #     print(f.read())
    # print(run_command)

    call(run_command)

    # check if need to zip
    if os.path.isdir(result_file):
        file_name = 'Result-' + NAME + '-' + file_name.split('.')[0] + '.zip'
        call(['zip', '-rv9', file_name, result_file])
    else:
        file_name = result_file
    return file_name


def upload_file(file, input_file):
    path = input_file.split('/')
    path[-1] = file.split('/')[-1]
    s3_key = '/'.join(path)
    try:
        s3.upload_file(file, UPLOADBUCKET, s3_key)
    except botocore.exceptions.ClientError as err:
        logger.warn(err)
    except Exception as err:
        logger.debug(traceback.format_exc())
        logger.error('Unexpected error happend will upload file')
        logger.err(err)


if __name__ == '__main__':
    pull_files(QUEUEURL)
