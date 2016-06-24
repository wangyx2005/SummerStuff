'''
This is a non-while-true version of grunt_node.py for testing purpose
'''

from nodeconfig import *
from grunt_node import *

future_job = {'test': Queue()}
service = {'ip': 'http://192.168.99.100:9901', 'name': 'test'}
resource = {'test': Queue()}
resource['test'].put(service)
working_job = Queue()
finished_job = Queue()

pull_files(QUEUEURL, future_job)

submit_processing(future_job, resource, working_job)

check_status(working_job, finished_job, resource, future_job, wait_time=0)

upload_result(finished_job, OUTPUT)
