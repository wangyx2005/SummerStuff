# this is image for using python3 wordcount

FROM ubuntu:14.04

MAINTAINER Yuxing Wang 'wangyx2005@gmail.com'

# Libraries
RUN apt-get -y update && apt-get install -y \
    build-essential \
    python \
    python-dev \
    python-distribute \
    python-pip

# Install AWS CLI

RUN pip install awscli boto3 

WORKDIR /home/yx

COPY wordcount.py /home/yx/wordcount.py

CMD python wordcount.py

