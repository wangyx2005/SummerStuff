from __future__ import print_function
import boto3
import json

print('Loading lambda function')

sqs = boto3.client('sqs')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    QueueUrl = '%(queue_url)s'
    sqs.send_message(QueueUrl=QueueUrl, MessageBody=json.dumps(event))

    # add ec2 machine into ecs default cluster
    instances = ec2.create_instances(ImageId='%(image_id)s', MinCount=1, KeyName='%(key_pair)s',
                                     SecurityGroups='%(security_group)s', InstanceType='%(instance_type)s',
                                     SubnetId='%(subnet_id)s', IamInstanceProfile={'Name': '$(iam_name)s'})

    # TODO: registe instances for cloudwater shutdown

    # wait instance running before start task
    instances[0].wait_until_running()

    # run ecs task
    ecs.run_task(taskDefinition='%(task_name)s', count=1)

    return 'send messages to sqs and start ecs'
