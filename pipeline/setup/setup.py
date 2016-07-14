import json
from zipfile import ZipFile
from time import sleep
import sys

import boto3
from botocore.exceptions import ClientError
from haikunator import Haikunator

from image_class import image
from _config import *

WAIT_TIME = 5

name_generator = Haikunator()

LAMBDA_EXEC_ROLE_NAME = 'lambda_exec_role'

LAMBDA_EXEC_ROLE = {
    "Statement": [
        {
            "Action": [
                "logs:*",
                "cloudwatch:*",
                "lambda:invokeFunction",
                "sqs:SendMessage",
                "ec2:Describe*",
                "ec2:StartInsatnces",
                "ecs:RunTask"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:logs:*:*:*",
                "arn:aws:lambda:*:*:*:*",
                "arn:aws:sqs:*:*:*",
                "arn:aws:ec2:*:*:*",
                "arn:aws:cloudwatch:*:*:*",
                "arn:aws:ecs:*:*:*"
            ]
        }
    ],
    "Version": "2012-10-17"
}


LAMBDA_EXECUTION_ROLE_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}


def _get_task_credentials():
    credentials = {}
    credentials['AWS_DEFAULT_REGION'] = 'us-east-1'
    credentials['AWS_DEFAULT_OUTPUT'] = 'json'
    credentials['AWS_ACCESS_KEY_ID'] = AWSAccessKeyId
    credentials['AWS_SECRET_ACCESS_KEY'] = AWSSecretKey
    return credentials

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


def _add_permission_s3_sqs(queue, account_id):
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
{
    "%(config_name)s": [
        {
            "%(config_arn)s": "%(FunctionArn)s",
            "Events": [
                "s3:ObjectCreated:*"
            ]
        }
    ]
}
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


def _add_permission_s3_lambda(s3_name, lambda_arn):
    lm = boto3.client('lambda')
    source = 'arn:aws:s3:::' + s3_name
    func = lm.get_function(FunctionName=lambda_arn)['Configuration']
    lm.add_permission(FunctionName=func['FunctionName'], StatementId='Allow_s3_invoke', Action='lambda:InvokeFunction', Principal='s3.amazonaws.com', SourceArn=source)


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
            'FunctionArn': event_arn, 'config_name': 'LambdaFunctionConfigurations', 'config_arn': 'LambdaFunctionArn'}
        _add_permission_s3_lambda(name, event_arn)
    elif option == 'sqs':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'QueueConfigurations', 'config_arn': 'QueueArn'}
    elif option == 'sns':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'TopicConfigurations', 'config_arn': 'TopicArn'}
    else:
        print('option needs to be one of the following: labmda, sqs, sns')
        return

    config = json.loads(config)

    boto3.client('s3').put_bucket_notification_configuration(
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


def _create_lambda_exec_role():
    '''
    create lambda_exec_role that allowing lambda function to acess s3,
    sqs, start ec2 and register cloudwatch
    '''
    # create role
    iam = boto3.client('iam')
    policy = json.dumps(LAMBDA_EXECUTION_ROLE_TRUST_POLICY, sort_keys=True)

    try:
        res = iam.get_role(LAMBDA_EXEC_ROLE_NAME)
        _policy = res['Role']['AssumeRolePolicyDocument']
        if _policy is not None and json.dumps(policy) == policy:
            pass
        else:
            iam.update_assume_role_policy(
                RoleName=LAMBDA_EXEC_ROLE_NAME, PolicyDocument=policy)

    except ClientError:
        print('creating role %s', LAMBDA_EXEC_ROLE_NAME)
        iam.create_role(RoleName=LAMBDA_EXEC_ROLE_NAME,
                        AssumeRolePolicyDocument=policy)
        res = iam.get_role(LAMBDA_EXEC_ROLE_NAME)

    # add policy
    exec_policy = json.dumps(LAMBDA_EXEC_ROLE, sort_keys=True)

    res = iam.list_role_policies(RoleName=LAMBDA_EXEC_ROLE_NAME)

    found = False
    for name in res['PolicyNames']:
        found = (name == 'LambdaExec')
        if found:
            break

    if not found:
        iam.put_role_policy(RoleName=LAMBDA_EXEC_ROLE_NAME, PolicyName='LambdaExec', PolicyDocument=exec_policy)


def _get_role_arn(role_name):
    '''
    '''
    try:
        res = boto3.client('iam').get_role(RoleName=role_name)
    except ClientError as e:
        print(e)
        print('Does not have role %s, make sure you have permission on creating iam role and run create_lambda_exec_role()', role_name)

    return res['Role']['Arn']


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


# def _add_permission_for_lambda():
#     '''
#     add permission for lambda function allowing acess to s3,
#     sqs, start ec2, register cloudwatch
#     '''
#     # TODO
#     pass


def _create_deploy_package(lambda_code, zipname):
    '''
    generate the deploy package
    '''
    # TODO: check correctness
    with open('lambda_function.py', 'w+') as run_file:
        run_file.write(lambda_code)
    with ZipFile(zipname, 'w') as codezip:
        codezip.write('lambda_function.py')


def _create_lambda_func(zipname):
    '''
    create lambda function
    '''
    # code = io.BytesIO()
    # with ZipFile(code, 'w') as z:
    #     with ZipFile(zipname, 'r') as datafile:
    #         for file in datafile.namelist():
    #             z.write(file)
    with open(zipname, 'rb') as tmpfile:
        code = tmpfile.read()
    name = name_generator.haikunate()
    role = _get_role_arn(LAMBDA_EXEC_ROLE_NAME)
    res = boto3.client('lambda').create_function(FunctionName=name, Runtime='python2.7', Role=role, Handler='lambda_function.lambda_handler', Code={'ZipFile': code}, Timeout=10, MemorySize=128)
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


def pipeline_setup(request, sys_info, clean):
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
    request['sqs'] = sqs.url

    # set ecs task
    image = get_image_info(request['name'])
    # info only need port, variables, UPLOADBUCKET & sqs.url
    info = {}
    info['port'] = request['port']
    info['variables'] = request['variables']
    # Changable, need to change on senquential run
    info['UPLOADBUCKET'] = request['output_s3_name']
    # QueueUrl
    info['QUEUEURL'] = sqs.url

    # generate task definition
    credentials = _get_task_credentials()
    task = _generate_task_definition(image, info, credentials)
    clean['task'].append(task)

    print(json.dumps(task, sort_keys=True, indent='    '))

    # set lambda
    code = _generate_lambda(image, sys_info, request, task['taskDefinition']['family'])

    zipname = request['name'] + name_generator.haikunate() + '.zip'
    _create_deploy_package(code, zipname)
    lambda_arn = _create_lambda_func(zipname)

    # set s3
    input_s3 = _get_or_create_s3(request['input_s3_name'])
    sleep(5)
    _set_event(input_s3, lambda_arn, 'lambda')

    output_s3 = _get_or_create_s3(request['output_s3_name'])
    print('You will get your result at %s' % output_s3)

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

    print(json.dumps(sys_info, sort_keys=True, indent='    '))

    clean = {}
    clean['sqs'] = []
    clean['task'] = []
    clean['lambda'] = []
    clean['cloudwatch'] = _get_or_create_queue('shutdown_alarm_sqs')

    if user_request['process']['type'] == 'single_run':
        request = {}
        request.update(user_request['process']['algorithms'][0])
        request['input_s3_name'] = user_request['input_s3_name']
        request['output_s3_name'] = user_request['output_s3_name']
        request['sqs'] = name_generator.haikunate()
        request['alarm_sqs'] = clean['cloudwatch'].url
        print(json.dumps(request, sort_keys=True, indent='    '))
        pipeline_setup(request, sys_info, clean)

    with open('clean_up.json', 'w+') as tmpfile:
        json.dump(clean, tmpfile, sort_keys=True, indent='    ')


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as tmpfile:
        user_request = json.load(tmpfile)
    main(user_request)
