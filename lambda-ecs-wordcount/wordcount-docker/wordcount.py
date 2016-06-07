from __future__ import print_function
import boto3
import uuid
import json

UPLOADBUCKET = 'wyx-wordcount-results'


def word_count(filepath):
    wordcount = {}
    with open(filepath, 'r') as f:
        for line in f:
            words = line.split()
            for word in words:
                if word not in wordcount:
                    wordcount[word] = 0
                wordcount[word] += 1
    return len(wordcount)

if __name__ == '__main__':
    print('Receiving message from SQS')
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
    QueueUrl = 'https://sqs.us-east-1.amazonaws.com/261965710151/wordcount-queue'

    # retrive messages from aws SQS, then parse the message to get
    # the s3 information, then run word_count and output file to s3 bucket
    msgs = sqs.receive_message(QueueUrl=QueueUrl, MaxNumberOfMessages=10)
    for msg in msgs['Messages']:
        record = json.loads(msg['Body'])['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
        s3.download_file(bucket, key, download_path)
        word_num = word_count(download_path)
        result_file = '/tmp/result_' + key
        with open(result_file, 'w+') as f:
            f.write('file %s has %d different words' % (key, word_num))
        s3.upload_file(result_file, UPLOADBUCKET, 'result_' + key)
        sqs.delete_message(QueueUrl=QueueUrl, ReceiptHandle=msg['ReceiptHandle'])
        print('file %s has %d different words' % (key, word_num))
