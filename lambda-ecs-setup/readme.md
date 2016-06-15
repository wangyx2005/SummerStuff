#### **Step 1: Set up S3 bucket**
started by setting up two S3 bucket to hold the input file and the result
```shell
$ aws s3 mb s3://container-clouds-input
make_bucket: s3://container-clouds-input/
$ aws s3 mb s3://container-clouds-output
make_bucket: s3://container-clouds-output/
```

#### **Step 2: Create an SQS queue**
create an SQS to pass the file information which is put in the s3 to ecs container. Record the QueueUrl, this will be used for the Lambda function setup.
```shell
$ aws sqs create-queue --queue-name container-clouds-queue

{
    "QueueUrl": "https://queue.amazonaws.com/183351756044/container-clouds-queue"
}
```
Then get the arn for this sqs queue by run the following command, also record the QueueArn.
```shell
$ aws sqs get-queue-attributes --queue-url https://queue.amazonaws.com/183351756044/container-clouds-queue --attribute-name QueueArn
{
    "Attributes": {
        "QueueArn": "arn:aws:sqs:us-east-1:183351756044:container-clouds-queue"
    }
}
```

#### **Step 3: Create the docker image**
In this step, a image with file operations wrapper is created from your imaging process (or other job) docker image, this wrapper simply runs a python script which download the file from input S3 bucket and uploaded files to output S3 bucket. 

First, a script *runscript.py* is created to handler the download/upload inside the container. A shell script version of such script will be also be provided later.

```python
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
    s3.download_file(bucket, key, DOWNLOAD_PATH)
    # run your job script
    subprocess.call(<your job run command>)
    s3.upload_file(RESULT_PATH, UPLOADBUCKET, RESULT_PATH)
    sqs.delete_message(QueueUrl=QUEUEURL, ReceiptHandle=msg['ReceiptHandle'])
    print('Job on file %s has finished' % key)

``` 

Then, we build the image with wrapper by creating a new dockerfile. In the docker file, the first RUN command is to setup libraries for python, for most cases, you should already have python and pip for your task image, then you can just omit this command. the second RUN command is to download AWS command line interface(awscli) and boto3, a python libary for aws sevices. The last thing is to copy the *runscript.py* that handler the download/upload work inside the container.  

```dockerfile
FROM <your processing image>

MAINTAINER Yuxing Wang 'wangyx2005@gmail.com'

# Libraries for python
RUN apt-get -y update && apt-get install -y \
    build-essential \
    python \
    python-dev \
    python-distribute \
    python-pip \
    zip

# Install AWS CLI

RUN pip install awscli boto3

WORKDIR /home/yx

COPY runscript.py /home/yx/runscript.py

CMD python runscript.py 
```

Then build the image with command:
```shell
$ docker build -t <image name> .
```
Tag it and upload the image. You can use Amazon EC2 Container Registry (ecr) if you want to keep this image private.
```shell
$ docker tag <image name>:<version> <your user id>/<image name>:<version>
$ docker push <your user id>/<image name>:<version>
```

#### **Step 4: Create ECS task**
Suppose you have already have an ECS cluster running and you have a Docker image ready after finishing previous step, you can create an ECS task definition.

```javascript
{
    "containerDefinitions": [
        {
            "volumesFrom": [],
            "memory": <make sure you allocate enough memory for your job>,
            "extraHosts": null,
            "dnsServers": null,
            "disableNetworking": null,
            "dnsSearchDomains": null,
            "portMappings": [],
            "hostname": null,
            "essential": true,
            "entryPoint": null,
            "mountPoints": [],
            "name": "<your task name>",
            "ulimits": null,
            "dockerSecurityOptions": null,
            "environment": [
                {
                    "name": "AWS_ACCESS_KEY_ID",
                    "value": "<your aws access key id>" 
                },
                {
                    "name": "AWS_SECRET_ACCESS_KEY",
                    "value": "<your aws secret access key>"
                },
                {
                    "name": "AWS_DEFAULT_REGION",
                    "value": "<your aws region>"
                },
                {
                    "name": "AWS_DEFAULT_OUTPUT",
                    "value": "json"
                },
                {
                    "name": "UPLOADBUCKET",
                    "value": "container-clouds-output" //<your upload bucket name>
                },
                {
                    "name": "QUEUEURL"
                    "value": "https://queue.amazonaws.com/183351756044/container-clouder-queue" //<the QueueUrl you got in the step 2>
                }
            ],
            "links": null,
            "workingDirectory": null,
            "readonlyRootFilesystem": null,
            "image": <your Docker image repo>,
            "command": null,
            "user": null,
            "dockerLabels": null,
            "logConfiguration": null,
            "cpu": 128, // 128/1024 share of CPU this task got if multi-container is running on a instance
            "privileged": null
        }
    ],
    "volumes": [],
    "family": "<your family task name>"
}
```
It is worthly notice that the "family" attribute is the task name you will use in the Lambda function setup.

Alternatively, you can use awscli to register the task definition:

```shell
$ aws ecs register-task-definition --cli-input-json file://register-task-definition.json
```

for security reason, you should create an **IAM role** that is only allow access to the SQS and S3 you are using for this setup and give the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY of such role in the *register-task-definition.json* file.

// Do I need this?
#### **Step 5: Add a policy to your ECS instance role that allows access to SQS and S3**

#### **Step 5: Create the Lambda function**
From the aws Lambda console [https://console.aws.amazon.com/lambda](https://console.aws.amazon.com/lambda), create a new lambda function.

1. skip the blueprint.
2. choose **S3** as **Event source type**, the bucket that is created for input file for the **Bucket** and **Object Created** for **Event type**.
3. choose **Runtime** as **Python 2.7**. The following code snippe will send messages to the sqs queue you just created and start your image process container.

```python
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

In **Role**, create a new role that allows this lambda function to invoke function, send message through sqs and run task on ecs. The following snippet is an sample role configuration.

```javascript
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

#### **Step 6: Add permission for S3 to allow S3 trigger lambda function**


#### **Step 7: test your services using lambda test**
