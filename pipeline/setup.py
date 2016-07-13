import json
from zipfile import ZipFile
import sys

import boto3
from haikunator import Haikunator

from image_class import image

name_generator = Haikunator()


def _get_task_credentials():
    credentials = {}
    from _config.py import *
    credentials['AWS_DEFAULT_REGION'] = 'us-east-1'
    credentials['AWS_DEFAULT_OUTPUT'] = 'json'
    credentials['AWS_ACCESS_KEY_ID'] = AWSAccessKeyId
    credentials['AWS_SECRET_ACCESS_KEY'] = AWSSecretKey

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


def _get_or_create_s3(name):
    '''
    create s3 bucket if not existed
    rtype: string
    '''
    if not _is_s3_exist(name):
        boto3.client('s3').create_bucket(Bucket=name)
        print('create s3 bucket %s.' % name)
    else:
        print('find s3 bucket %s.' % name)
    return name


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
        print('option needs to be one of the following: labmda, sqs, sns')
        return

    print(config)

    boto3.client('s3').put_bucket_nofification_configuration(
        Bucket=name, NotificationConfiguration=config)

    print('finish setup s3 bucket %s event notification' % name)


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
    {
        'taskDefinition': {
            'taskDefinitionArn': 'string',
            'containerDefinitions': [...],
            'family': 'string',
            'revision': 123,
            'volumes': [
                {
                    'name': 'string',
                    'host': {
                        'sourcePath': 'string'
                    }
                },
            ],
            'status': 'ACTIVE'|'INACTIVE',
            'requiresAttributes': [
                {
                    'name': 'string',
                    'value': 'string'
                },
            ]
        }
    }
    '''
    image_info.init_all_variables(user_info, credentials)
    task_def = image_info.generate_task()
    task = boto3.client('ecs').register_task_definition(family=task_def[
        'family'], containerDefinitions=task_def['containerDefinitions'])
    # task name: task_def['family']
    return task


def _delete_task_definition(task):
    # should be wrong
    # TODO: find the correct way to delete task
    boto3.client('ecs').deregister_task_definition(taskDefinition=task)

# iam


# lambda

def _generate_lambda(image, sys_info, request, task_name):
    '''
    generate lambda function using lambda_run_task_template
    para: image: the informations about using a image
    type: image_class.image_info

    para: sys_info: other system info, see _get_sys_info()
    type: dict

    rtype: string
    '''
    lambda_para = {}
    lambda_para['instance_type'] = image.instance_type
    lambda_para['task_name'] = task_name
    lambda_para.update(request)
    lambda_para.update(sys_info)
    with open('lambda_run_task_template', 'r') as tmpfile:
        lambda_func = tmpfile.read()
    return lambda_func % lambda_para


def _add_permission_for_lambda():
    '''
    add permission for lambda function allowing acess to s3,
    sqs, start ec2, register cloudwatch
    '''
    # TODO
    pass


def _create_deploy_package(lambda_code, name):
    '''
    generate the deploy package
    '''
    # TODO: check correctness
    with open('lambda_run.py', 'w+') as run_file:
        run_file.write(lambda_code)
    with ZipFile(name, 'w+') as codezip:
        codezip.write('lambda_run.py')


def _create_lambda_func(zipname, ):
    '''
    create lambda function
    '''
    codezip = ZipFile(zipname, 'r')
    name = name_generator.haikunate()
    role = ''
    res = boto3.client('lambda').create_function(FunctionName=name, Runtime='python2.7', Role=role, Handler='lambda_run.lambda_handler', Code={'ZipFile':codezip}, Timeout=10, MemorySize=128)
    codezip.close()
    return res['FunctionArn']


def _deleta_lambda(name):
    boto3.client('lambda').delete_function(FunctionName=name)


# utilities for setting up the whole thing
def get_image_info(name):
    '''
    based on the name of the user request, find the image inforomation
    para name: algorithm name
    type: string

    rpara: the infomation of a algorithm, see
    rtype: image_class.image_info
    '''
    # TODO: need to be rewrite down the road
    file_name = name + '_info.json'
    with open('../algorithms/' + file_name, 'r') as tmpfile:
        info = image(json.load(tmpfile))
    return info


def _get_sys_info(key_pair, account_id, region):
    '''
    prepare the system information (non-task specific informations) including
    ec2 image_id, key_pair, security_group, subnet_id, iam_name, region,
    accout_id for making the lambda function.

    rtype dict
    '''
    # TODO: need rewrite this function
    info = {}
    info['image_id'] = 'ami-8f7687e2'
    info['iam_name'] = 'ecsInstanceRole'
    info['subnet_id'] = 'subnet-d32725fb'
    info['security_group'] = 'launch-wizard-13'
    info['key_pair'] = key_pair
    info['region'] = region
    info['account_id'] = account_id
    return info


def pipeline_setup(request, sys_info):
    '''
    based on the user request, set up the whole thing.
    para: request:
    {
        "name": "",
        "port": [],
        "sqs": "",
        "alarm_sqs": "",
        "input_s3_name": "",
        "output_s3_name": "",
        "variables":
        {
            "name": "value"
        }
    }
    type: json

    para:sys_info

    '''
    # set sqs
    sqs = _get_or_create_queue(request['sqs'])

    # set ecs task
    image = get_image_info(request['name'])
    # info = user_request['process']['algorithms'][0]
    info = {}
    info['variables'] = request['variables']
    # Changable, need to change on senquential run
    info['UPLOADBUCKET'] = request['output_s3_name']
    # QueueUrl
    info['QUEUEURL'] = sqs.url

    # generate task definition
    credentials = _get_task_credentials()
    task = _generate_task_definition(image, info, credentials)

    # set lambda
    code = _generate_lambda(image, sys_info, request)
    _create_deploy_package(code)
    lambda_arn = _create_lambda_func()

    # set s3
    input_s3 = _get_or_create_s3(request['input_s3_name'])
    _set_event(input_s3, lambda_arn, 'lambda')

    output_s3 = _get_or_create_s3(request['output_s3_name'])
    print('You will get your result at %s', output_s3)

    # finish setup
    print('You can start upload files')


def main(user_request):
    '''
    parse the user_request json
    para: user_request
    type: json

    support only 'single_run' for now
    '''
    sys_info = _get_sys_info(user_request['key_pair'], user_request[
                             'account_id'], user_request['region'])

    if user_request['process']['type'] == 'single_run':
        request = {}
        request.update(user_request['process']['algorithms'][0])
        request['input_s3_name'] = user_request['input_s3_name']
        request['output_s3_name'] = user_request['output_s3_name']
        request['sqs'] = name_generator.haikunate()
        request['alarm_sqs'] = 'shutdown_alarm_sqs'
        clean = pipeline_setup(request, sys_info)

    with open('clean_up.json', 'w+') as tmpfile:
        json.dump(clean, tmpfile, sort_keys=True, indent='    ')


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as tmpfile:
        user_request = json.load(tmpfile)
    main(user_request)
