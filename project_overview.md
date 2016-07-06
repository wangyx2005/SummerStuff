### Algorithm Developer:
- docker container
- a json file contains the following info:
    * Memory requirement
    * system it is running
    * expected input file location
    * expected output file location
    * expected user-specified environment variables
    * expected exposed port number

-------------------------------------------------------------
System:
System will wrap it with a python program read information from 'sqs', download file from 'input_s3' to expected input file location and upload result file to 'upload_s3', expose port number, environment variables + 'input_s3' + 'output_s3' + 'sqs' + user aws id/key to access s3. Upload new container. 
**50 % supported**


### User:

##### simple parallel one-algorithm run
- a json file contains input / output s3 bucket names, algorithms, user-specified environment variables and aws id/key
- once get notify start upload, start upload files

-------------------------------------------------------------
System:
- read aws id/key
- create s3 bucket.
- create a sqs (not expose to user)
- based on algorithm container json file (how should I get it?) and user-specified environment variables, create a ecs task, return the names.
**not supported yet, easy to implement** 
- create a lambda function what watch s3 bucket that do the following: 
    * start a number of machines and wait until those running
    * upload the file information to sqs
    * run task
    * register the machines on cloudWatch to shut down **not supported yet**
- notify user to start upload.

**pros**: very scalable
**cons**: 
* if a task fails, very hard to track it. To fix it, add logging mechanism
* security, you have to allow every container access s3. 

--------------------------------------------------------------
System work with master and :
with master nodes: try to fix the previous cons, give only master node access to S3
- read aws id/key
- create sqs for file info(not expose to user)
- create s3 bucket to push notification to sqs.
- create sqs for service (not expose to user)
- based on algorithm container json file (how should I get it?) and user-specified environment variables, create a ecs task, return the names.
**not supported yet, easy to implement**
** user start a master node, input ecs task list via environment variable **
- master node:
    * pull from sqs
    * add more machines, start ecs task **not supported yet, easy to implement**
    * pull from sqs for service info
    * assign task
    * if task fails, assign another.

**cons**: scalability


### grunt:
- security
- running forever