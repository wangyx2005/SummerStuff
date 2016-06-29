import os

import threading
from queue import Queue

from grunt_node import *
from _nodeconfig import *

UPLOADBUCKET = os.getenv('UPLOADBUCKET', default=OUTPUT)
FILEURL = os.getenv('FILEURL', default=FILEURL)
IPURL = os.getenv('IPURL', default=IPURL)
log_lvl = os.getenv('LOG_LVL', default='INFO')
service_num = os.getenv('NUM_SERVICES')

if service_num == None:
    logging.error('Do not have environment variable NUM_SERVICES')
    return

# FILEURL = 'https://sqs.us-east-1.amazonaws.com/183351756044/container-clouder-queue'
# UPLOADBUCKET = 'container-clouds-output'

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console = logging.StreamHandler()

if log_lvl == 'ERROR':
    console.setLevel(logging.ERROR)
elif log_lvl == 'WARNING':
    console.setLevel(logging.WARNING)
elif log_lvl == 'DEBUG':
    console.setLevel(logging.DEBUG)
else:
    console.setLevel(logging.INFO)

console.setFormatter(formatter)

logger.addHandler(console)

if __name__ == '__main__':
    # future_job = {'test': Queue()}
    # resource = {'test': Queue()}
    # working_job = Queue()
    # finished_job = Queue()
    # service = {'ip': 'http://192.168.99.100:9901', 'name': 'test'}
    # resource['test'].put(service)

    future_job = {}
    resource = {}
    working_job = Queue()
    finished_job = Queue()

    t0 = threading.Thread(target=pull_service,
                          args=(IPURL, resource, future_job))
    t0.start()

    t1 = threading.Thread(target=pull_files, args=(
        FILEURL, future_job, service_num))
    t1.start()

    t2 = threading.Thread(target=submit_processing, args=(
        future_job, resource, working_job))
    t2.start()

    t3 = threading.Thread(target=check_status, args=(
        working_job, finished_job, resource, future_job))
    t3.start()

    t4 = threading.Thread(target=upload_result,
                          args=(finished_job, UPLOADBUCKET))
    t4.start()
