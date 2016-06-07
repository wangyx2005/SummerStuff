from __future__ import print_function
import boto3
import json

print('Loading lambda function')

sqs = boto3.client('sqs')


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    QueueUrl = 'https://sqs.us-east-1.amazonaws.com/261965710151/wordcount-queue'
    sqs.send_message(QueueUrl=QueueUrl, MessageBody=json.dumps(event))
