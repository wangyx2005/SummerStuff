import json
import sys

SUPPORTED_SYSTEM = {'ubuntu'}


def generate_dockerfile(system_name, container_name):
    if system_name == 'ubuntu':
        with open('ubuntu_wrapper', 'r') as myfile:
            dockerfile = myfile.read()
    return dockerfile % {'container_name': container_name}


def show_dockerfile(system_name, container_name):
    print(generate_dockerfile(system_name, container_name))


def generate_runscript(input_path, output_path, name, command):
    with open('runscript_template', 'r') as myfile:
        script = myfile.read()
    return script % {'input': input_path, 'output': output_path, 'name': name, 'command': command}


def show_runscript(input_path, output_path, name, command):
    print(generate_runscript(input_path, output_path, name, command))


def wrapper(alg_info):
    '''
    automatic generate dockerfile
    para: a json object contains necessory information about algorithm
    type: json
    '''
    # generate runscript
    if alg_info['input_file_path'][-1] != '/':
        alg_info['input_file_path'] += '/'

    runscript = generate_runscript(alg_info['input_file_path'], alg_info[
                                   'output_file_path'], alg_info['name'],
                                   alg_info['run_command'])
    with open('runscript.py', 'w') as tmpfile:
        tmpfile.write(runscript)

    # generate dockerfile
    if alg_info['system'] not in SUPPORTED_SYSTEM:
        print("not support %s yet." % alg_info['system'])
        return
    dockerfile = generate_dockerfile(
        alg_info['system'], alg_info['container_name'])
    dockerfile_name = alg_info['name'] + '.Dockerfile'
    with open(dockerfile_name, 'w') as tmpfile:
        tmpfile.write(dockerfile)

    return dockerfile_name


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please input at least one file')

    for file_name in sys.argv[1:]:
        with open(file_name, 'r') as data_file:
            alg = json.load(data_file)
        wrapper(alg)
