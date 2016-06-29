FROM python:3.5-slim
MAINTAINER Yuxing Wang <wangyx2005@gmail.com>

RUN pip install boto3 requests

COPY _config.py _config.py
COPY service.py service.py

CMD python service.py