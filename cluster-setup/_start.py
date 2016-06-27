'''
this module is to lounch ec2 machines to 'default' cluster of ecs
'''
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from _awsconfig import *

ACCESS_ID = DEFAULT_ACCESS_KEY_ID
SECRET_KEY = DEFAULT_SECRET_KEY

IMAGE_ID = DEFAULT_IMAGE_ID
SIZE_ID = 't2.micro'

Driver = get_driver(Provider.EC2)
conn = Driver(ACCESS_ID, SECRET_KEY, region=DEFAULT_REGION)


# Here we select size and image
def start(num, size_id, image_id=DEFAULT_IMAGE_ID, key_pair=DEFAULT_KEY_PAIR, subnet_id=DEFAULT_SUBNET):
    nodes = []
    sizes = conn.list_sizes()
    size = [s for s in sizes if s.id == SIZE_ID][0]

    image = conn.get_image(image_id)

    subnet = [net for net in conn.ex_list_subnets() if net.name ==
              subnet_id][0]

    nodes.append(conn.create_node(name='test-node', image=image, size=size, ex_mincount=num
                                  ex_subnet=subnet, ex_keyname=DEFAULT_KEY_PAIR, ex_iamprofile=DEFAULT_IAM))

    return nodes


def destroy_cluster(nodes):
    for node in nodes:
        conn.destroy_node(node)
    print('Successfully terminate all nodes in the cluster')


def destroy_node(node, nodes):
    for n in nodes:
        if node == n:
            conn.destroy_node(node)
            nodes.remove(n)
