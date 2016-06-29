This is a **"cheated"** service discovery, all it do is to find the host ip address of the ec2 instance in the subnet, submit the ip address and port number, service name which are passed in via environment variable to a sqs queue

the environment variable passed in for `docker run` command:
```
PORT
SERVICE_NAME
IPURL (optional)
REGION (optional)

