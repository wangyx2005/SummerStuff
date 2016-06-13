# this is image for using python wordcount

FROM ubuntu:14.04

MAINTAINER Yuxing Wang 'wangyx2005@gmail.com'

# Libraries
RUN apt-get -y update && apt-get install -y \
    build-essential \
    git \
    python \
    python-dev \
    python-distribute \
    python-pip

#install numpy && SimpleITK 

RUN pip install -f http://www.simpleitk.org/SimpleITK/resources/software.html SimpleITK && \
    pip install numpy

RUN mkdir -p /home/jporter && cd /home/jporter && \
    git clone https://github.com/justinrporter/nodule-seg.git && \
    mkdir -p /home/jporter/nodule-seg/media_root/init && \
    mkdir -p /home/jporter/nodule-seg/logs

COPY 0c2b8406cd8ca33af1130c3c91cfb70b2797df7a.nii  /home/jporter/nodule-seg/media_root/init/

# Install AWS CLI && boto3
RUN pip install awscli boto3 

WORKDIR /home/jporter/nodule-seg/scripts

CMD sh segment_one.batch
