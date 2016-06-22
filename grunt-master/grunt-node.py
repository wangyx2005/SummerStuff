import requests
from queue import Queue
from boto3 import client
import json
import subprocess
import os
import logging
from time import wait


'''
for information about grunt, see https://github.com/Mayo-QIN/grunt
'''

UPLOADBUCKET = os.getenv('UPLOADBUCKET')
QUEUEURL = os.getenv('QUEUEURL')

def pull_file(message_URL, future_job, wait_time=10):
    sqs = client('sqs')
    msgs = sqs.receive_message(QueueUrl=message_URL)
    while 'Messages' not in msgs:
        msgs = sqs.receive_message(QueueUrl=message_URL)
        wait(wait_time)
