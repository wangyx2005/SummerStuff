import json

import boto3
from haikunator import Haikunator

from image_class import image_info

name_generator = Haikunator()


# SQS related

def _get_or_create_queue(name):
    '''
    get queue by name, if the queue doesnot exist, create one.
    rtype: sqs.Queue
    '''
    resource = boto3.resource('sqs', )
    if _is_sqs_exist(name):
        return resource.get_queue_by_name(QueueName=name)
    else:
        return resource.create_queue(QueueName=name)


def _is_sqs_exist(name):
    '''
    check existense of a given queue
    para: name: sqs name
    type: string
    '''
    queues = boto3.client('sqs').list_queues()
    for queue in queues['QueueUrls']:
        if name in queue:
            if name == queue.split('/')[-1]:
                return True
    return False


def _delete_queue(queue):
    queue.delete()


def _add_permission(queue, account_id):
    '''
    add permission to allow s3 put information into sqs
    para: queue
    type: sqs.Queue

    para: account_id: user aws account id
    type: string
    '''
    label = 'S3-SQS' + '-' + name_generator.haikunate()
    queue.add_permission(Label=label, AWSAccountIds=[account_id],
                         Actions=['SendMessage'])

    # change permission to allow everyone, cannot add such permisssion directly
    # ref: https://forums.aws.amazon.com/thread.jspa?threadID=223798
    policy = json.loads(queue.attributes['Policy'])
    new_policy = policy
    new_policy['Statement'][0]['Principal'] = '*'
    queue.set_attributes(Attributes={'Policy': json.dumps(new_policy)})


# S3
S3_EVENT_CONFIGURATIONS = '''
%(config_name)s: [
    {
        'LambdaFunctionArn': %(FunctionArn)s,
        'Events': [
            's3:ObjectCreated:*'
        ],
    },
]
'''


def _is_s3_exist(name):
    '''
    check for existense
    '''
    s3 = boto3.client('s3')
    for bucket in s3.list_buckets()['Buckets']:
        if name == bucket['Name']:
            return True
    return False


def get_or_create_s3(name):
    '''
    create s3 bucket if not existed
    '''
    if not _is_s3_exist(name):
        boto3.client('s3').create_bucket(Bucket=name)
        print('create s3 bucket %s.' % name)
    else:
        print('find s3 bucket %s.' % name)


def _set_event(name, event_arn, option):
    '''
    set s3 create object to event notification.
    para: name: s3 bucket name
    type: string
    para: event_arn: arn of the event source
    type: string
    para: option: one of these 'lambda', 'sqs', 'sns'
    type: string
    '''
    if option == 'lambda':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'LambdaFunctionConfigurations'}
    elif option == 'sqs':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'QueueConfigurations'}
    elif option == 'sqs':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'TopicConfigurations'}
    else:
        print('option needs to be one of the following three: labmda, sqs, sns')
        return

    print(config)

    boto3.client('s3').put_bucket_nofification_configuration(
        Bucket=name, NotificationConfiguration=config)

    print('finish setup s3 bucket %s event notification' % name)


# lambda


# ecs
def _generate_task_definition(image_info, user_info, credentials):
    '''
    Based on the algorithm information and the user running information,
    generate task definition
    para image_info: all the required info for running the docker container
    type: image_info class
    para: user_info: passed in information about using the algorithm.
    user_info: {'port' : [], 'variables' = {}}
    type: json

    rtype json
    '''
    image_info.init_all_variables(user_info, credentials)
    task_def = image_info.generate_task()
    task = boto3.client('ecs').register_task_definition(family=task_def[
        'family'], containerDefinitions=task_def['containerDefinitions'])
    return task


def _delete_task_definition(task):
    # should be wrong
    boto3.client('ecs').deregister_task_definition(taskDefinition=task)


# 