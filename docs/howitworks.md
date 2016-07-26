### General

### Wrap



### Run
To achieve high scalability, we disassemble complex work flow into two part: single algorithm processing and information transfers between algorithms.


For each single algorithm processing, a microservice is built around it on AWS:
- a lambda function is used to monitor the input event. It can be triggered by a file upload to the input file s3 bucket event or invoked by called from other lambda functions. Once it is triggered, it send the information of the input file to a message queue and start a ecs task to start algorithm processing.
- a message queue is used to hold the information about the input files.
- a ecs task is used to perform the actual algorithm processing on the cloud. It retrieve the input file information from the message queue, download from sources and process the files. Once it is finished, the resulting file is upload to another s3 bucket and the ecs task is terminated.

