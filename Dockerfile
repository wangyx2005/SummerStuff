# this is image for 

FROM ubuntu:14.04

MAINTAINER Yuxing Wang 'wangyx2005@gmail.com'

# Libraries
RUN apt-get -y update && apt-get install -y \
    maven \
    git \
    openjdk-8-jdk \
    openjdk-8-jre \
    wget
