from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from _awsconfig import *

ACCESS_ID = DEFAULT_ACCESS_KEY_ID
SECRET_KEY = DEFAULT_SECRET_KEY

IMAGE_ID = DEFAULT_IMAGE_ID
SIZE_ID = 't1.micro'

cls = get_driver(Provider.EC2)
driver = cls(ACCESS_ID, SECRET_KEY, region="us-east-1")

# Here we select size and image
sizes = driver.list_sizes()
images = driver.list_images()

size = [s for s in sizes if s.id == SIZE_ID][0]
image = [i for i in images if i.id == IMAGE_ID][0]

# node = driver.create_node(name='test-node', image=image, size=size)
