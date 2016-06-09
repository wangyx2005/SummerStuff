from __future__ import print_function
import boto3
import uuid
import json

print('Loading lambda function')

s3 = boto3.client('s3')


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


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # get the object from the event and perform wordcount
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        #print(bucket)
        key = record['s3']['object']['key']
        #print(key)
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
        #print(download_path)
        print('downloading file')

        s3.download_file(bucket, key, download_path)
        words = word_count(download_path)
        print('file %s has %d different words' % (key, words))
