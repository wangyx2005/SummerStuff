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
System will wrap it with a python program download file from 'input_s3' to expected input file location and upload result file to 'upload_s3', expose port number, environment variables + 'input_s3' + 'output_s3' + user aws id/key to access s3. Upload new container. 
** 50 % supported **


### User:
##### simple parallel multi-algorithm run
- a json file contains input / output s3 bucket names, algorithms, user-specified environment variables and aws id/key
-------------------------------------------------------------
System:
- create s3 bucket. (Do we need this?)
- based on algorithm container json file and user-specified environment variables, create a ecs task, return the names.
** not supported yet, easy to implement ** 
- create a lambda function that do the following:
    * 