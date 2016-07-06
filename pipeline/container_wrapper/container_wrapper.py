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
    return script


def show_runscript(input_path, output_path, name, command):
    print(generate_runscript(input_path, output_path, name, command))


def wrapper(alg_info):
    # generate dockerfile
    if alg_info['system'] not in SUPPORTED_SYSTEM:
        print("not support %s yet." % alg_info['system'])
        return
    dockerfile = generate_dockerfile(alg_info['system'], alg_info['container_name'])
    dockerfile_name = alg_info['name'] + '.Dockerfile'
    with open(dockerfile_name, 'w') as tmpfile:
        tmpfile.write(dockerfile)

    if alg_info['input_file_path'][-1] != '/':
        alg_info['input_file_path'] += '/'


if __name__ == '__main__':
    if len(sys.argv) 