import threading
from queue import Queue
from grunt_node import *
import os

UPLOADBUCKET = os.getenv('UPLOADBUCKET')
QUEUEURL = os.getenv('QUEUEURL')

if __name__ == '__main__':
    future_job = {'test': Queue()}
    resource = {'test': Queue()}
    working_job = Queue()
    finished_job = Queue()
    service = {'ip': 'http://grunttest:9901', 'name': 'test'}
    resource['test'].put(service)

    t1 = threading.Thread(target=pull_files, arg=(QUEUEURL, future_job))
    t1.start()

    t2 = threading.Thread(target=submit_processing, arg=(
        future_job, resource, working_job))
    t2.start()

    t3 = threading.Thread(target=check_status, arg=(
        working_job, finished_job, resource, future_job))
    t3.start()

    t4 = threading.Thread(target=upload_result,
                          arg=(finished_job, UPLOADBUCKET))
    t4.start()
