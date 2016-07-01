'''
this module is to lounch ec2 machines to 'default' cluster of ecs
'''
from libcloud.compute.types import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.providers import get_driver

from haikunator import Haikunator

from _awsconfig import *

ACCESS_ID = DEFAULT_ACCESS_KEY_ID
SECRET_KEY = DEFAULT_SECRET_KEY

IMAGE_ID = DEFAULT_IMAGE_ID
SIZE_ID = 't2.micro'

Driver = get_driver(Provider.EC2)
conn = Driver(ACCESS_ID, SECRET_KEY, region=DEFAULT_REGION)

name_generater = Haikunator()

# Here we select size and image


def start(num, size_id, image_id=DEFAULT_IMAGE_ID, key_pair=DEFAULT_KEY_PAIR, subnet_id=DEFAULT_SUBNET, securty_group=DEFAULT_SECURITY_GROUP):
    node_dict = {}
    sizes = conn.list_sizes()
    size = [s for s in sizes if s.id == SIZE_ID][0]

    image = conn.get_image(image_id)

    subnet = [net for net in conn.ex_list_subnets() if net.name ==
              subnet_id][0]

    group = [group for group in conn.ex_list_security_groups() if group ==
             securty_group]

    for _ in range(num):
        name = name_generater.haikunate()
        while name in node_dict:
            name = name_generater.haikunate()
        node = conn.create_node(name=name, image=image, size=size, ex_subnet=subnet,
                                ex_keyname=DEFAULT_KEY_PAIR, ex_iamprofile=DEFAULT_IAM, ex_security_groups=group)
        node_dict[name] = node

    return node_dict


def destroy_cluster(node_dict):
    for node_name in node_dict.keys():
        conn.destroy_node(node_dict.pop(node_name))
    print('Successfully terminate all nodes in the cluster')


def destroy_node(node_name, node_dict):
    if node_name not in node_dict:
        print('No such node in the cluster')
    else:
        node = node_dict.pop(node_name)
        conn.destroy_node(node)


def stop_cluster(node_dict):
    for node in node_dict.values():
        conn.ex_stop_node(node)
    print('stop all machines in the cluster')


def stop_node(node_name, node_dict):
    if node_name not in node_dict:
        print('No such node in the cluster')
    else:
        conn.ex_stop_node(node_dict[node_name])


def start_cluster(node_dict):
    for node in node_dict.values():
        conn.ex_start_node(node)


def start_node(node_name, node_dict={}):
    if node_name not in node_dict:
        print('No such node in the cluster')
    else:
        conn.ex_stop_node(node_dict[node_name])


def start_by_name(node_name):
    nodes = [node for node in conn.list_nodes() if node.name == node_name]
    for node in nodes:
        conn.ex_start_node(node)


def stop_by_name(node_name):
    nodes = [node for node in conn.list_nodes() if node.name == node_name]
    for node in nodes:
        conn.ex_stop_node(node)


def _wait_for_state(node, state):
    '''
    state includes running, stopped, terminated
    '''
    while True:
        if node.state == NodeState.RUNNING and state == 'RUNNING':
            break
        if node.state == NodeState.STOPPED and state == 'STOPPED':
            break
        if node.state == NodeState.TERMINATED and state == 'TERMINATED':
            break
