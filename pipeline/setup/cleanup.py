import json

import boto3

session = boto3.session.Session()


def _delete_queue(queue_url):
    boto3.client('sqs').delete_queue(QueueUrl=queue_url)


def _delete_s3(bucket):
    '''
    all objects in the bucket must be deleted before a bucket can be deleted
    '''
    _delete_all_objects(bucket)
    boto3.client('s3').delete_bucket(Bucket=bucket)


def _delete_all_objects(bucket):



def _delete_task(task_arn):
    boto3.client('ecs').deregister_task_definition(taskDefinition=task_arn)


def _deleta_lambda(lambda_arn):
    boto3.client('lambda').delete_function(FunctionName=lambda_arn)


def _delete_alarm(alarm_name):
    boto3.client('cloudwatch').delete_alarms(AlarmNames=[alarm_name])


if __name__ == '__main__':
    with open('clean_up.json', 'r') as tmpfile:
        info = json.load(tmpfile)

    for sqs in info['sqs']:
        _delete_queue(sqs)

    for task_arn in info['task']:
        _delete_task(task_arn)

    for lambda_arn in info['lambda']:
        _deleta_lambda(lambda_arn)

    for s3 in info['s3']:
        _delete_s3(s3)

    