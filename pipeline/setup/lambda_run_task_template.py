from __future__ import print_function
import boto3
import json
from time import time

print('Loading lambda function')

sqs = boto3.client('sqs')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')
cw = boto3.client('cloudwatch')


def find_container(cluster, instance_id):
    i = 1
    while True:
        ins = ecs.list_container_instances(cluster=cluster)
        ins = ecs.describe_container_instances(cluster=cluster, containerInstances=ins['containerInstanceArns'])
        ins = ins['containerInstances']
        for info in ins:
            if info['ec2InstanceId'] == instance_id:
                return info['containerInstanceArn']
        # print('run {} times'.format(i))
        # i += 1



def lambda_handler(event, context):
    start_time = time()
    # print("Received event: " + json.dumps(event, indent=2))

    QueueUrl = '%(sqs)s'
    sqs.send_message(QueueUrl=QueueUrl, MessageBody=json.dumps(event))

    # add ec2 machine into ecs default cluster
    instances = ec2.create_instances(ImageId='%(image_id)s', MinCount=1,
                                     KeyName='%(key_pair)s', MaxCount=1,
                                     SecurityGroups=['%(security_group)s'],
                                     InstanceType='%(instance_type)s',
                                     # SubnetId='%(subnet_id)s',
                                     IamInstanceProfile={'Name': '%(iam_name)s'})

    # TODO: registe instances for cloudwatch shutdown
    alarm_name = instances[0].id + '-shutdown'
    alarm_act = ['arn:aws:swf:%(region)s:%(account_id)s:action/actions/AWS_EC2.InstanceId.Terminate/1.0']
    dimension = [{"Name": "InstanceId", "Value": instances[0].id}]
    cw.put_metric_alarm(AlarmName=alarm_name, AlarmActions=alarm_act,
                        MetricName='CPUUtilization', Namespace='AWS/EC2',
                        Statistic='Average', Dimensions=dimension, Period=300,
                        EvaluationPeriods=2,
                        Threshold=1, ComparisonOperator='LessThanThreshold')

    # send the cloudwatch name for cleanup
    sqs.send_message(QueueUrl='%(alarm_sqs)s', MessageBody=alarm_name)
    print('run time {}'.format((time() - start_time)))

    # wait instance running before start task
    instances[0].wait_until_running()
    print('wait uitil ec2 running. run time {}'.format((time() - start_time)))

    # run ecs task
    arn = find_container('default', instances[0].id)
    print('find container time run time {}'.format((time() - start_time)))

    ecs.start_task(taskDefinition='%(task_name)s', containerInstances=[arn])

    print('run time {}'.format((time() - start_time)))
    return 'send messages to sqs and start ecs'
