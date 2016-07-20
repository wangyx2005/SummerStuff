### General
This is an automatic setup tool for setting up the data analysis pipeline on the AWS. It provides utility functions to facilitate algorithm developer to build their analytical tools in docker container, published them for others to use and users to use those analytical tools to facilitate their analysis.

The __container_wrapper__ folder contains all the utility functions for algorithm developers and __setup__ folder is for user to submit their analytical workflows. 
Once new algorithm has been added, __algorithms__ folder will be created to save the detailed information about the algorithm


### for algorithm developers
Have your algorithm containerized, summit a json file describe your algorithm.
For json file template, see __Algorithm_submit_template.json__. For example of json files, see __Algorithm_submit_example.json__
Run the following command to wrap your container to fit the requirement of running using our tool on AWS. By default, a public container image repo hosting the revised will be uploaded to Docker Hub.
```
python container_wrapper.py your_json_file
```


### for algorithm user
Make sure you have full access to **Lambda**, **Simple Queue Services**, **S3**, **EC2 Container Services**, **CloudWatch** and **EC2**.
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
                "ec2:*",
                "ecs:*",
                "iam:PassRole",
                "ecs:RunTask"
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
You can added manually on aws console or run the following command. 
```
``` 



#### TODO list:
- one to all / all to one algorithm setup
- workflow language
- optimize usage of lambda function
- add support to upload container images to places other than Docker hub