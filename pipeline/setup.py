import json

import boto3
from haikunator import Haikunator

name_generator = Haikunator()

# SQS related

def _get_or_create_queue(name):
    '''
    get queue by name, if the queue doesnot exist, create one.

    rtype: sqs.Queue
    '''
    resource = boto3.resource('sqs')
    if _is_sqs_exist(name):
        return resource.get_queue_by_name(QueueName=name)
    else:
        return resource.create_queue(QueueName=name)


def _is_sqs_exist(name):
    '''
    check existense of a given queue
    name:

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

def _is