#### * Step 1: Set up S3 bucket *
started by setting up two S3 bucket to hold the input file and the result
```
$ aws s3 mb s3://container-clouds-input
make_bucket: s3://container-clouds-input/
$ aws s3 mb s3://container-clouds-output
make_bucket: s3://container-clouds-output/
```

#### * Step 2: Create an SQS queue *
create an SQS to pass the file information which is put in the s3 to ecs container. Record the QueueUrl, this will be used for the Lambda function setup.
```
aws sqs create-queue --queue-name container-clouder-queue

{
    "QueueUrl": "https://queue.amazonaws.com/183351756044/container-clouder-queue"
}
```
Then get the arn for this sqs queue by run the following command, also record the QueueArn.
```
$ aws sqs get-queue-attributes --queue-url https://queue.amazonaws.com/183351756044/container-clouder-queue --attribute-name QueueArn
{
    "Attributes": {
        "QueueArn": "arn:aws:sqs:us-east-1:183351756044:container-clouder-queue"
    }
}
```

#### * Step 3: Create the Lambda function *
From the aws Lambda console [https://console.aws.amazon.com/lambda](https://console.aws.amazon.com/lambda), create a new lambda function.

1. skip the blueprint.
2. choose * S3 * as * Event source type *, the bucket that is created for input file for the * Bucket * and * Object Created * for * Event type *.
3. choose * Runtime * as * Python 2.7 *. The following code snippe will send messages to the sqs queue you just created and start your image process container.
```
from __future__ import print_function
import boto3
import json

print('Loading lambda function')

sqs = boto3.client('sqs')
ecs = boto3.client('ecs')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    QueueUrl = https://queue.amazonaws.com/183351756044/container-clouder-queue"
    sqs.send_message(QueueUrl=QueueUrl, MessageBody=json.dumps(event))
    ecs.run_task(taskDefinition='wordcount-task', count=1)
    
    return 'send messages to sqs and start ecs'
```
In * Role *, create a new role that allows this lambda function to invoke function, send message through sqs and run task on ecs. The following snippet is an sample role configuration.
```
{
    "Statement": [
        {
            "Action": [
                "logs:*", 
                "lambda:invokeFunction",
                "sqs:SendMessage",
                "ecs:RunTask"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:logs:*:*:*",
                "arn:aws:lambda:*:*:*:*",
                "arn:aws:sqs:us-east-1:183351756044:container-clouder-queue",
                "arn:aws:ecs:*:*:*"
            ]
        }
    ],
    "Version": "2012-10-17"
}
```

