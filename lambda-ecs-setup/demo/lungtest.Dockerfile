# this is image for lung segmentation image processing task, please check https://github.com/justinrporter/nodule-seg for more details about this task

FROM ubuntu:14.04

MAINTAINER Yuxing Wang 'wangyx2005@gmail.com'

# Libraries
RUN apt-get -y update && apt-get install -y \
    build-essential \
    git \
    python \
    python-dev \
    python-distribute \
    python-pip \
    python-scipy

# update numpy, scipy and SimpleITK
RUN pip install numpy && \
    pip install -f http://www.simpleitk.org/SimpleITK/resources/software.html SimpleITK 

RUN mkdir -p /home/jporter && cd /home/jporter && \
    git clone https://github.com/justinrporter/nodule-seg.git && \
    mkdir -p /home/jporter/nodule-seg/media_root/init && \
    mkdir -p /home/jporter/nodule-seg/media_root/logs

# omit for the real job, just try to make calculation quicker for demo purpose.
RUN cd /home/jporter/nodule-seg/scripts && \
    sed -e 's/500/5/' segment_one.batch > tmp.batch && \
    sed -e 's/"0c2b8406cd8ca33af1130c3c91cfb70b2797df7a.nii"/$1/' tmp.batch > segment.batch && \
    rm tmp.batch

# COPY 0c2b8406cd8ca33af1130c3c91cfb70b2797df7a.nii  /home/jporter/nodule-seg/media_root/init/

# Install AWS CLI && boto3
# RUN pip install awscli boto3 

WORKDIR /home/jporter/nodule-seg/scripts

CMD sh segment.batch
