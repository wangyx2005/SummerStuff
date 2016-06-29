FROM python:3.5-slim
MAINTAINER "Yuxing Wang" <wangyx2005@gmail.com>

RUN pip install boto3 requests && \
    mkdir -p /data/source && \
    mkdir -p /data/result

WORKDIR /data

COPY grunt_node.py grunt_node.py
COPY run.py run.py
COPY _nodeconfig.py _nodeconfig.py

CMD python run.py