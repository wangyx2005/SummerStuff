import logging
import os

import boto3
import requests

def main(region=DEFAULT_REGION):
    sqs = boto3.client('sqs', region=DEFAULT_REGION)



if __name__ == '__main__':
    DEFAULT_REGION = os.getenv('REGION', default='us-east-1')
    main()
