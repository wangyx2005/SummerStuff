FROM wangyx2005/lungtest

MAINTAINER "Yuxing Wang" wangyx2005@gmail.com

# Install AWS CLI

RUN apt-get install -y zip

RUN pip install awscli boto3

COPY runscript.py /home/jporter/nodule-seg/scripts/runscript.py

CMD python runscript.py