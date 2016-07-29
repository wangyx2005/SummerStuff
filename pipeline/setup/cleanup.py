import json

import boto3
from botocore.exceptions import ClientError


def _delete_queue(queue_url):
    boto3.client('sqs').delete_queue(QueueUrl=queue_url)


def _delete_s3(bucket):
    '''
    all objects in the bucket must be deleted before a bucket can be deleted
    '''
    _delete_all_objects(bucket)
    boto3.client('s3').delete_bucket(Bucket=bucket)


def _delete_all_objects(bucket):
    pass


def _delete_task(task_arn):
    boto3.client('ecs').deregister_task_definition(taskDefinition=task_arn)


def _deleta_lambda(lambda_arn):
    boto3.client('lambda').delete_function(FunctionName=lambda_arn)


def _delete_alarm(alarm_name):
    boto3.client('cloudwatch').delete_alarms(AlarmNames=[alarm_name])


def _delete_lambda_log(lambda_arn):
    name = '/aws/lambda/' + lambda_arn.split(':')[-1]
    boto3.client('logs').delete_log_group(logGroupName=name)


if __name__ == '__main__':
    with open('clean_up.json', 'r') as tmpfile:
        info = json.load(tmpfile)

    for sqs in info['sqs']:
        _delete_queue(sqs)

    for task_arn in info['task']:
        _delete_task(task_arn)

    for lambda_arn in info['lambda']:
        _deleta_lambda(lambda_arn)
        _delete_lambda_log(lambda_arn)

    # for s3 in info['s3']:
    #     _delete_s3(s3)

    sqs = info['cloudwatch']

    msgs = {}
#    empty_msgs = '''\{'ResponseMetadata': \{'HTTPStatusCode': 200, 'RequestId': '([a-z0-9]*-){4}[a-z0-9]*', \}\}'''

    while len(msgs) == 0:
        try:
            msgs = boto3.client('sqs').receive_message(QueueUrl=sqs)

            _delete_alarm(msgs['Messages'][0]['Body'])
            boto3.client('sqs').delete_message(
                QueueUrl=sqs, ReceiptHandle=msgs['Messages'][0]['ReceiptHandle'])
            msgs = {}
        except ClientError as err:
            msgs = boto3.client('sqs').receive_message(QueueUrl=sqs)
            print(err)
        except KeyError:
            if len(msgs) == 1 and 'ResponseMetadata' in msgs and \
                    'HTTPStatusCode' in msgs['ResponseMetadata'] and \
                    msgs['ResponseMetadata']['HTTPStatusCode'] == 200:
                _delete_queue(sqs)
                break
            else:
                print(msgs)
                raise

    print('Successfully clean up everything')
