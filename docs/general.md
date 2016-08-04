## General
This is an automatic setup tool for setting up the data analysis pipeline on the AWS. It provides utility functions to facilitate algorithm developer to build their analytical tools in docker container, published them for others to use and users to use those analytical tools to facilitate their analysis.

This tool is developed on Python 3.5.1. Using this on previous versions of python 3 or python 2 has not been tested.

Now cloud_pipe is on Pypi, and it supports pip. To install cloud_pipe,
`pip install cloud_pipe`. After install cloud_pipe:

To submit an algorithm or bring your analyze tool, use `wrap -d`. For more options, check:
```
wrap --help
```
You will see the following options:

```
usage: wrap-script.py [-h] [-d] [-f FILES [FILES ...]] [-s] [-r REGISTRY]
                      [-u USER]

A tool to wrap your containers

optional arguments:
  -h, --help            show this help message and exit
  -d, --describe        use command line editor to describe your algorithm
  -f FILES [FILES ...], --files FILES [FILES ...]
                        List json files to describe your algorithms
  -s, --show            show described algorithm before generate new container
  -r REGISTRY, --registry REGISTRY
                        the registry where you want to upload the container,
                        default is Docker hub
  -u USER, --user USER  user name of docker hub account, default is wangyx2005
```

To run single algorithm or deploy you analytical work flow, use `setup-pipe -f your-workflow-json`. For more options, check: 
```
setup-pipe --help
```
You will see the following options:

```
usage: setup-pipe-script.py [-h] [-uu] [-f FILES [FILES ...]]

A tool to set up your pipeline

optional arguments:
  -h, --help            show this help message and exit
  -uu, --use_user_credential
                        use user credential to run ecs task, we suggest using
                        a less privileged user for running ecs. For more
                        information, see our docs
  -f FILES [FILES ...], --files FILES [FILES ...]
                        json files to describe your work flow
```

To clean up your resources on the AWS after finishing your runs, use `clean`.
If you are using a multiple step work flow, all your intermedia files stays for your future references.
You do not need to do the clean up, as in our current setup, AWS will not charge you anything for the set up if you are not running anything except S3 storage for your results.
Performing the clean up just to keep your AWS console neat.
