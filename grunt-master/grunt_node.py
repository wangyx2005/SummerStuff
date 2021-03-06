import json
import os
import logging
from time import sleep
from queue import Queue
import traceback

import requests
import requests.exceptions
import boto3.session
import botocore.exceptions

'''
for information about grunt, see https://github.com/Mayo-QIN/grunt
'''

logger = logging.getLogger(__name__)
log_lvl = os.getenv('LOG_LVL', default='WARNING')

if log_lvl == 'ERROR':
    logger.setLevel(logging.ERROR)
elif log_lvl == 'INFO':
    logger.setLevel(logging.INFO)
elif log_lvl == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

JOB_DICT = \
    {
        'ip': '',
        'job_id': '',
        'source_file_name': '',
        'result_file_name': '',
        'source_file_path': '',
        'result_file_path': '',
        'service_name': '',
    }

RESOURCE_DICT = \
    {
        'ip': '',
        'name': ''
    }

WAITTIME = os.getenv('WAITTIME', default=5)
STREAM_SIZE = os.getenv('STREAM_SIZE', default=32)


def pull_service(message_URL, resource, future_job, region='us-east-1', wait_time=WAITTIME):
    '''
    pull service information from message_url, add serivce into resource and
    future_job queue
    '''
    session = boto3.session.Session(region_name=region)
    sqs = session.client('sqs')
    while True:
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
                logger.error('Unexpected error occures at pull_service()!!')
                logger.error(err)
            if 'Messages' not in msgs:
                sleep(wait_time)

        logger.info('receive ip info from SQS')
        for msg in msgs['Messages']:
            info = json.loads(msg['Body'])

            # add service into resource
            service = {}
            service['ip'] = 'http://' + info['ip'] + ':' + info['port']
            service['name'] = info['service_name']
            if service['name'] not in resource:
                resource[service['name']] = Queue()
            resource[service['name']].put(service)
            logger.info('add service %s into resource', service['name'])

            # add service into future_job
            if service['name'] not in future_job:
                future_job[service['name']] = Queue()

            # delete received message
            try:
                sqs.delete_message(QueueUrl=message_URL,
                                   ReceiptHandle=msg['ReceiptHandle'])
            except botocore.exceptions.ClientError as err:
                logger.debug(traceback.format_exc())
                logger.warn(err.response)
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error(
                    'Unexpected error occures when delete message at pull_service()')
                logger.error(err)
            logger.info('delete one message from ip_queue')


def pull_files(message_URL, future_job, service_num, wait_time=WAITTIME, region='us-east-1'):
    session = boto3.session.Session(region_name=region)
    s3 = session.client('s3', region)
    sqs = session.client('sqs', region)

    # wait untill all services has been registered
    while len(future_job) < int(service_num):
        sleep(wait_time)

    while True:
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
            if 'Messages' not in msgs:
                sleep(wait_time)

        logger.info('receive file info from SQS')
        for msg in msgs['Messages']:
            record = json.loads(msg['Body'])['Records'][0]
            bucket = record['s3']['bucket']['name']
            file = record['s3']['object']['key']
            # print(file)
            job = dict(JOB_DICT)
            # just parse the real file name
            job['source_file_name'] = file.split('/')[-1]
            # print(job['source_file_name'])
            job['source_file_path'] = 'source/' + job['source_file_name']
            job['bucket'] = bucket

            try:
                s3.download_file(bucket, file, 'source/' +
                                 job['source_file_name'])
            except Exception as err:
                # This part has problem. formate is wrong
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
            logger.info('download file %s from S3 bucket',
                        job['source_file_name'])
            for job_queue in future_job.values():
                job_queue.put(dict(job))
                logger.info('add job to future_job queue')

            # delete received message
            try:
                sqs.delete_message(QueueUrl=message_URL,
                                   ReceiptHandle=msg['ReceiptHandle'])
            except botocore.exceptions.ClientError as err:
                logger.debug(traceback.format_exc())
                logger.warn(err.response)
            except Exception as err:
                logger.debug(traceback.format_exc())
                logger.error('Unexpected error occures when delete message!!')
                logger.error(err)
            logger.info('delete one message from file queue')


def submit_job(future_job, resource, working_job, service_num, wait_time=WAITTIME):
    # service['ip'] already contains 'http://'
    req_ses = requests.Session()

    # wait untill all services has been registered
    while len(future_job) < int(service_num):
        sleep(wait_time)

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
                response = req_ses.post(
                    service['ip'] + '/rest/service/runJob', files=file, data=para)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                # TODO: add failed numbers for checking resource health
                # if cannot connect to service, put back for later use
                logger.warn('Cannot submit job %s on service %s at %s' % (job[
                            'source_file_name'], service_name, service['ip']))
                logger.warn(err)
                resource[service_name].put(service)
                future_job[service_name].put(job)
                continue
            except FileNotFoundError as err:
                logger.warn('Cannot find source file: %s',
                            job['source_file_path'])
                resource[service_name].put(service)
                future_job[service_name].put(job)
                continue
            except Exception as err:
                logger.error('Unexpect error occurs on processing job %s on service %s at %s' % (job[
                             'source_file_name'], service_name, service['ip']))
                logger.error(err)
                continue

            logger.info('submit job %s to service %s at %s' %
                        (job['source_file_name'], service_name, service['ip']))

            # put successful job into working job
            job['job_id'] = response.json()['uuid']
            job['ip'] = service['ip']
            job['result_file_name'] = result_file_name
            job['result_file_path'] = 'result/' + result_file_name
            job['service_name'] = service['name']
            working_job.put(job)
            logger.info('add a job to working_job queue')

        sleep(wait_time)


def check_status(working_job, finished_job, resource, future_job, wait_time=WAITTIME):
    req_ses = requests.Session()
    while True:
        job = working_job.get()
        # check status
        try:
            status = req_ses.get(job['ip'] + '/rest/job/' + job['job_id'])
            status.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.warn(err)
            working_job.put(job)
            continue
        except Exception as err:
            logger.error('Unexpected error occurs on check_status')
            continue
        size = working_job.qsize()
        # print(status.json()['status'])
        service = {}
        if status.json()['status'] == 'success':
            finished_job.put(job)
            service['name'] = job['service_name']
            service['ip'] = job['ip']
            resource[service['name']].put(service)
            logger.info('job %s finished on service %s at %s' %
                        (job['source_file_name'], job['service_name'], service['ip']))
        # TODO: check the running status
        elif status.json()['status'] == 'running':
            working_job.put(job)
            logger.debug('job %s running on service %s' %
                         (job['source_file_name'], job['service_name']))
        # restart the job
        else:
            future_job[job['service_name']].put(job)
            service['name'] = job['service_name']
            service['ip'] = job['ip']
            resource[service['name']].put(service)

        sleep(wait_time / (size + 1))


def upload_result(finished_job, result_bucket, region='us-east-1', stream_size=STREAM_SIZE):
    session = boto3.session.Session(region_name=region)
    s3 = session.client('s3', region)
    req_ses = requests.Session()

    while True:
        job = finished_job.get()
        url = job['ip'] + '/rest/job/' + job['job_id'] + '/file/output'
        try:
            result = req_ses.get(url, stream=True)
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.warn(err)
            finished_job.put(job)
            continue
        except Exception as err:
            logger.error('Unexpeced error happend in retrieve file %s from %s'
                         % (job['result_file_name'], job['ip']))
            logger.error(err)
            continue
        # save result at local
        with open(job['result_file_path'], 'wb') as f:
            for chunk in result.iter_content(chunk_size=stream_size):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        logger.info('retrieve file %s', job['result_file_name'])

        # upload file to s3 bucket
        try:
            s3.upload_file(job['result_file_path'],
                           result_bucket, job['result_file_name'])
        except botocore.exceptions.ClientError as err:
            logger.warn(err)
            finished_job.put(job)
        except Exception as err:
            logger.debug(traceback.format_exc())
            logger.error('Unexpected error happend will upload file')
            logger.err(err)
        logger.info('upload file %s to s3 bucket %s' %
                    (job['result_file_name'], result_bucket))

        os.remove(job['result_file_path'])
        logger.info('remove file %s', job['result_file_name'])
