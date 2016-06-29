import logging
import os
import json
from time import sleep

import boto3
import requests

from _config import *

'''
This module get port number, service_name from environment variable
get host ip address and send these information to a sqs, which is also
passed through environment variable.
message form:
{
    'ip': 'XXX.XXX.XXX.XX',
    'port': '9901',
    'service_name':
}
'''

URL = 'http://169.254.169.254/latest/meta-data/local-ipv4'


def main(myregion, mysqs):
    # get ip address of the ec2 instance
    while True:
        ip = requests.get(URL)
        if ip.status_code == 200:
            ip = ip.text
            break

    port = os.getenv('PORT')
    if port is None:
        logging.error('Do not have environment variable PORT')
        return
    name = os.getenv('SERVICE_NAME')
    if name is None:
        logging.error('Do not have environment variable SERVICE_NAME')
        return

    # send message to sqs
    sqs = boto3.client('sqs', myregion)
    msg = {}
    msg['ip'] = ip
    msg['port'] = port
    msg['service_name'] = name
    sqs.send_message(QueueUrl=mysqs, MessageBody=json.dumps(msg))


if __name__ == '__main__':
    myregion = os.getenv('REGION', default=DEFAULT_REGION)
    mysqs = os.getenv('IPURL', default=DEFAULT_SQS)
    sleep(30)
    main(myregion, mysqs)
