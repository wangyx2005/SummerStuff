from __future__ import print_function
import boto3
import json
import subprocess
import os


UPLOADBUCKET = os.getenv('UPLOADBUCKET')
QUEUEURL = os.getenv('QUEUEURL')
RESULT_PATH = <your job result you want to upload>
DOWNLOAD_PATH = <Input path for your job script>

print('Receiving message from SQS')
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# retrive messages from aws SQS, then parse the message to get
# the s3 information, then run word_count and output file to s3 bucket
msgs = sqs.receive_message(QueueUrl=QUEUEURL, MaxNumberOfMessages=10)
for msg in msgs['Messages']:
    record = json.loads(msg['Body'])['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    # download your file
    s3.download_file(bucket, key, DOWNLOAD_PATH)
    # run your job script
    subprocess.call(['sh', '/home/jporter/nodule-seg/scripts/segment_one.batch'])
    # compress your output for upload
    filename = key.split('.')[0]

    s3.upload_file(RESULT_PATH, UPLOADBUCKET, RESULT_PATH)
    sqs.delete_message(QueueUrl=QueueUrl, ReceiptHandle=msg['ReceiptHandle'])
    print('Job on file %s has finished' % key)
