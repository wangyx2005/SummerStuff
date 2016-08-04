### For Algorithm User
#### Prerequisition on AWS

Make sure you have full access to **Lambda**, **Simple Queue Services**, **S3**, **EC2 Container Services**, **CloudWatch** and **EC2**. If you are using aws container registry to host container image, __EC2ContainerRegistry__ access will also be needed.

Here is a screen shot of the policies.



Additionally, make sure you have the following two roles in your IAM: __EC2ActionsAccess__ role with __CloudWatchActionsEC2Access__ policy and  __ecsInstanceRole__ role with __AmazonEC2ContainerServiceforEC2Role__ policy.

The former one allows AWS, more specifically, cloud watch to stop/terminate ec2 instance on your behave. The later one allows ec2 instance register to ecs cluster, poll images for ecr and write logs to CloudWatch log.
These two are will be automatically generated when you first use CloudWatch alarm and ecs if using the aws console. Here is a link about how to sent these up.


Lastly, create a role called __lambda_exec_role__ with the following policy:
```
{
    "Statement": [
        {
            "Action": [
                "logs:*",
                "cloudwatch:*",
                "lambda:invokeFunction",
                "sqs:SendMessage",
                "ec2:Describe*",
                "ec2:StartInsatnces",
                "ec2:RunInstances",
                "iam:PassRole",
                "ecs:StartTask",
                "ecs:ListContainerInstances",
                "ecs:DescribeContainerInstances"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:logs:*:*:*",
                "arn:aws:lambda:*:*:*",
                "arn:aws:sqs:*:*:*",
                "arn:aws:ec2:*:*:*",
                "arn:aws:cloudwatch:*:*:*",
                "arn:aws:ecs:*:*:*",
                "*"
            ]
        }
    ],
    "Version": "2012-10-17"
}
```
This role will allow lambda function to send input file information to message queue, check resources to start ecs task, launch ec2 instance into ecs cluster if needed and register ec2 on cloudwatch for shutdown.

You can added manually on aws console or run the following command. 
```
create-lambda-exec-role
```


#### Prepare your work flow json file
Right now you need to prepare your work flow json file directly. We will intergrate commen workflow language (cwl) to prepare work flow in the near future.





#### Run your work flow
Once a JSon file of your work flow description is generated, you can run your work flow on the cloud simply by running the following command.
```
setup-pipe -f work-flow-json
``` 

When the set up is finished, you will receive the following message. You can start uploading your input files and letting cloud handle the rest.
```
You can start upload files at some_S3_bucket_name
You will get your result at some_S3_bucket_name
```

Enjoy pipelining!!
