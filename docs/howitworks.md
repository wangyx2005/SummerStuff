## How it works
### Overview
This automatic toolbox for image processing is current build on AWS. The main computational work is done on Amazon EC2 Container Service ([Amazon ECS](https://aws.amazon.com/ecs/)). In our case, each image processing job (processing one file/image using one algorithm) is launched into separate ECS tasks on the ECS cluster, which can be scaled perfectly. 

Normally, an image processing work flow contains multiple algorithms and intermediate data transfer from one algorithm to another. This tool will also handle that for the users. All the intermediate data are stored in the S3 bucket for transfer and possible later use of users.

This tools also facilitates researchers to bring their own algorithms. To use your own algorithm, simply prepare it inside a Docker container, and push the image to Docker Hub or locally. Then, by using the container wrapper tool, you can describe all the details of your algorithm: including its command line options, user defined variables and required resources to run it. 

The following is the Amazon services we use to construct this automation:
- __[Amazon EC2 Container Service](https://aws.amazon.com/ecs/)__: Amazon ECS is a highly scalable, high performance container management service that supports Docker containers and allows user to easily run applications on a managed cluster of Amazon EC2 instances. 

AWS Lambda is a compute service that runs your code in response to events and automatically manages the compute resources for you, making it easy to build applications that respond quickly to new information. Lambda starts running your code within milliseconds of an event such as an image upload, in-app activity, website click, or output from a connected device.

### Wrap
In the area of imaging processing, researchers use various different algorithms to processing images. Therefore it is crucial to  


### Run
To achieve high scalability, we disassemble complex work flow into two part: single algorithm processing and information transfers between algorithms.


For each single algorithm processing, a microservice is built around it on AWS:
- a lambda function is used to monitor the input event. It can be triggered by a file upload to the input file s3 bucket event or invoked by called from other lambda functions. Once it is triggered, it send the information of the input file to a message queue and start a ecs task to start algorithm processing.
- a message queue, we use [Amazon Simple Queue Service (SQS)](https://aws.amazon.com/sqs/) is used to hold the information about the input files.
- a ecs task is used to perform the actual algorithm processing on the cloud. It retrieve the input file information from the message queue, download from sources and process the files. Once it is finished, the resulting file is upload to another s3 bucket and the ecs task is terminated.

picture

As each task is run on specific type of EC2 instance, the default ECS scheduler does not fit our need.
In our current version, lambda function is also in charge of checking resources to start ecs task, launch ec2 instance into ecs cluster if needed and register ec2 on cloudwatch for shutdown. This is not very efficient. In our future version, a customer scheduler will be added the substitute that part in lambda function. 