import json


class image_info:
    class port:
        def __init__(self, port_info):
            '''
            para: port_info: dict contains all port information
            type: dict
            '''
            self.host_port = None
            self.container_port = port_info['container_port']
            self.protocal = port_info['protocal']

        def add_default_port_mapping(self):
            self.host_port = self.container_port

    class variable:
        def __init__(self, var):
            '''
            para var: dict conatins all var information
            type: dict
            '''
            self.name = var['name']
            self.initialized = False
            self.required = var['required']
            self.value = None

        def init_var(self, value):
            self.value = value
            self.initialized = True



    def __init__(self, info):
        '''
        para info:
        type: json
        '''
        self.memory = info['memory']['suggested']
        self.name = info['name']
        self.image = info['image']
        self.cpu = None
        self.port = {}
        self.env_variable = {}

        for port_info in info['port']:
            self.port[port_info['port']] = port(port_info)

        for var in info['user_specified_environment_variables']:
            self.env_variable[var['name']] = variable(var)

    def init_all_variables():
        pass

    def add_required_variable(self, var_name):
        '''
        para vars: a list of required variables
        type: list
        '''
        self.env_variable[var_name] = variables()