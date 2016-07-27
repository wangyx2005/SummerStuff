## Quick Start
### For Algorithm Developers
Using this automatic tool for algorithm developers is very easy. 
All you need to do is two things: have your algorithm containerized and prepare a json file to describe your algorithm. 
Then running the following command to wrap your container to fit the requirement of running using our tool on AWS.
```
python container_wrapper.py your_json_file
``` 
By default, a public container image repo hosting the revised will be uploaded to Docker Hub. And a more detailed json file describe your algorithm is generated in ../algorithms folder for algorithm users to use.


#### Prepare your json file
Here is an example of the json file describing one algorithm
```
{
    "container_name": "wangyx2005/change123",
    "system": "ubuntu",
    "input_file_path": "/",
    "output_file_path": "/",
    "executable_path": "/change123",
    "run_command": "sh /change123.sh $input $output",
    "name": "change123-s3",
    "instance_type": "",
    "memory": 
    {
        "minimal": 50,
        "suggested": 128
    },
    "CPU":
    {

    },
    "user_specified_environment_variables": 
    [
        {
            "name": "TEST_ENV",
            "required": true
        }
    ],
    "port": 
    [
        {
            "port": 9090,
            "protocol": "tcp"
        }
    ]
}
```
Here is a more detailed explanation of each entry
- __container_name__: your containerized algorithm image. should be reachable from `docker pull`
- __system__: the system from which your image is built on. We currently support only ubuntu
- __run_command__: the command to run your algorithm. please substitute your input file with `$input`, output file/folder with `$output` and using the executable with the full path.
- __input_file_path__: the folder where input file should be
- __output_file_path__: the folder where output file should be
- __executable_path__: the full path of the executable
- __name__: A name which other algorithm user will refer this algorithm as. Need to be unique.

- __instance_type__: As algorithm developer, we believe you have a better understanding of your algorithm than anyone else. please suggest a instance type where this algorithm preferably running on on AWS.
- __memory__: the minimal and suggested memory requirement for running this algorithm container. You can omit minimal.
- __CPU__: 
- __user_specified_environment_variables__: this is the list of variable you allow other algorithm user to use, such as seed. 
- __port__: the port number your algorithm exposed.


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

```

#### Install requirements
This tool requires two third party libaries: boto3 and Haikunator. 
```
pip install -r requirements.txt
```

#### Describe your workflow



#### Run your workflow
Once 



