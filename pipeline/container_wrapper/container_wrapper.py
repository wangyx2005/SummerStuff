import json
import sys
import os
import errno
from subprocess import call

SUPPORTED_SYSTEM = {'ubuntu'}


def _generate_dockerfile(system_name, container_name):
    '''
    generate the dockerfile content
    '''
    if system_name == 'ubuntu':
        with open('ubuntu_wrapper', 'r') as myfile:
            dockerfile = myfile.read()
    return dockerfile % {'container_name': container_name}


def show_dockerfile(system_name, container_name):
    print(_generate_dockerfile(system_name, container_name))


def _generate_runscript(input_path, output_path, name, command):
    '''
    generate runscript that fetch information from sqs, handling
    download/upload file
    '''
    with open('runscript_template', 'r') as myfile:
        script = myfile.read()
    return script % {'input': input_path, 'output': output_path, 'name': name, 'command': command}


def show_runscript(input_path, output_path, name, command):
    print(_generate_runscript(input_path, output_path, name, command))


def wrapper(alg_info):
    '''
    automatic generate dockerfile
    para: a json object contains necessory information about algorithm
    type: json
    '''
    # generate runscript
    if alg_info['input_file_path'][-1] != '/':
        alg_info['input_file_path'] += '/'
    if alg_info['output_file_path'][-1] != '/':
        alg_info['output_file_path'] += '/'

    # create a folder with name for dockerfile & runscript
    try:
        os.makedirs(alg_info['name'])
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # generate runscript
    runscript = _generate_runscript(alg_info['input_file_path'], alg_info[
                                    'output_file_path'], alg_info['name'],
                                    alg_info['run_command'])
    with open(alg_info['name'] + '/runscript.py', 'w+') as tmpfile:
        tmpfile.write(runscript)

    # generate dockerfile
    if alg_info['system'] not in SUPPORTED_SYSTEM:
        print("not support %s yet." % alg_info['system'])
        return
    dockerfile = _generate_dockerfile(
        alg_info['system'], alg_info['container_name'])

    with open(alg_info['name'] + '/Dockerfile', 'w+') as tmpfile:
        tmpfile.write(dockerfile)


def _get_instance_type(alg_info):
    '''
    Based on the algorithm developer provided information, choose an
    apporperate ec2 instance_type
    '''
    # TODO: rewrite
    return 't2.micro'


def _generate_image(folder_name):
    '''
    build new docker image and upload, return new images
    '''
    # TODO: rewrite
    # PATH = '../algorithms/'
    # name = dockerfile_name.split('.')[0]
    name = folder_name
    tagged_name = 'wangyx2005/' + name
    BUILD_COMMAND = 'docker build -t %(name)s %(path)s/.' \
        % {'name': name, 'path': folder_name}
    TAG_COMMAND = 'docker tag %(name)s %(tag)s' % {
        'tag': tagged_name, 'name': name}
    UPLOAD_COMMAND = 'docker push %(tag)s' % {'tag': tagged_name}

    print(BUILD_COMMAND)

    call(BUILD_COMMAND.split())
    call(TAG_COMMAND.split())
    call(UPLOAD_COMMAND.split())

    # remove the folder generated during the image generatation process
    remove = 'rm -r ' + folder_name
    # call(remove.split())

    return tagged_name


def _generate_image_info(alg_info, container_name):
    '''
    generate wrapped image info for ecs task
    para: alg_info:
    type: json

    para: container_name: access name of the wrapped container
    type: string

    rtype: json
    '''
    # TODO:
    new_vars = []
    new_vars.append({'name': 'output_s3_name', 'required': True})
    new_vars.append({'name': 'sqs', 'required': True})
    new_vars.append({'name': 'LOG_LVL', 'required': False})
    new_vars.append({'name': 'NAME', 'required': True})
    new_vars.append({'name': 'AWS_DEFAULT_REGION', 'required': True})
    new_vars.append({'name': 'AWS_DEFAULT_OUTPUT', 'required': True})
    new_vars.append({'name': 'AWS_ACCESS_KEY_ID', 'required': True})
    new_vars.append({'name': 'AWS_SECRET_ACCESS_KEY', 'required': True})

    alg_info['container_name'] = container_name
    if alg_info['instance_type'] == '':
        alg_info['instance_type'] = _get_instance_type(alg_info)
    alg_info['user_specified_environment_variables'].extend(new_vars)
    return alg_info


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please input at least one file')

    for file_name in sys.argv[1:]:
        with open(file_name, 'r') as data_file:
            alg = json.load(data_file)
        wrapper(alg)

        container_name = _generate_image(alg['name'])

        info = _generate_image_info(alg, container_name)

        name = container_name.split('/')[-1] + '_info.json'

        with open('../algorithms/' + name, 'w') as data_file:
            json.dump(info, data_file, indent='    ', sort_keys=True)

        print('Successfully wrap given container')
