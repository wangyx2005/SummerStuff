import json

from haikunator import Haikunator

name_generator = Haikunator()


class image:
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

            # TODO
            def valid_entry():
                pass

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
        # TODO: this need to be changed
        self.cpu = 32
        self.port = {}
        self.env_variable = {}

        for port_info in info['port']:
            self.port[port_info['port']] = self.port(port_info)

        for var in info['user_specified_environment_variables']:
            self.env_variable[var['name']] = self.variable(var)

    def init_all_variables(self, info, credentials):
        '''
        Based on the user information provided, initialize all the entries
        para info:
        type: json
        '''
        for port_number in info['port']:
            self.port[port_number].add_default_port_mapping()

        for name, value in info['variables'].iteritems():
            self.env_variable[name].init_var(value)

        for name, value in credentials.iteritems():
            self.env_variable[name].init_var(value)

    def valid_info(self):
        '''
        check if such initialization is vaild. Namely, check if all required
        variable has been initializaed, if every variable meet its requirement.

        rtype: boolean
        '''
        for name, var in self['env_variable'].iteritems():
            if not var.vaild_entry():
                return False
            if var.required and var.initializaed:
                print("envoriment variable %s needs to be initialized", name)
                return False
        return True

    def add_required_variable(self, var_name):
        '''
        para vars: a list of required variables
        type: list
        '''
        helper = {}
        helper['name'] = var_name
        helper['required'] = True
        self.env_variable[var_name] = self.variable(helper)

    def generate_task(self):
        with open('ecs_task_definition_template.json', 'r') as tmpfile:
            template = json.load(tmpfile)
        template['containerDefinitions'][0]['memory'] = self.memory
        template['containerDefinitions'][0]['name'] = self.name
        template['containerDefinitions'][0]['image'] = self.image
        # TODO: change 32
        template['containerDefinitions'][0]['cpu'] = 32
        # add port
        for port in self.port.values():
            helper = {}
            helper['hostPort'] = port.host_port
            helper['containerPort'] = port.container_port
            helper['protocol'] = port.protocol
            template['containerDefinitions'][0]['port'].append(helper)
        # add environment variable
        for var in self.env_variable.iteritems():
            template['containerDefinitions'][0][
                'environment'][var['name']] = var['value']
        template['family'] = self.name + '-' + name_generator.haikunate()
