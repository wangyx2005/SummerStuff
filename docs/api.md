## yunpipe

PACKAGE CONTENTS:
    pipeline (package)
    scripts (package)
    utils
    wrapper (package)

### yunpipe.wrapper
PACKAGE CONTENTS
    container_wrapper

#### yunpipe.wrapper.container_wrapper

__describe_algorithm()__:
    command line editor of the detailed information of algorithm container.

    :rtype: json

__generate_all(alg, args)__:
    generate dockerfile, build new image, upload to registry and generate
    detailed information of the new image
 
    :para alg: algorthm information user provided
    :type: json
 
    :para agrs: command line argument from script.wrap. args.user and 
    args.registry

    :type: argparser object

__generate_dockerfile(system_name, container_name)__:
    generate the dockerfile content.
 
    Based on the system which user's prebuild image, generate dockerfile
    including adding run enviroment of runscript.py and add runscript.
 
    :para system_name: the system name in which the docker image is built on
    :tpye: string
 
    :para container_name: user's algorithm container
    :tpye: string
 
    :return: the dockerfile content.
    :rtype: string

__generate_image(name, folder_path, args)__:
    build new docker image and upload.
 
    giver new docker image name and dockerfile, build new image, tagged with
    user account and pushed to desired registry. Default registry is docker
    hub, will support other registry soon.
     
    :para name: new docker image name. Without tag and registry.
    :type: string
     
    :para folder_path: the path to tmp folder where stores dockerfiles.
    path is ~/.cloud_pipe/tmp/name
    :typr: string
     
    :para args: command line arguments passed in from scripts.wrap, currently
    only useful entry is user, will using registry soon
    :type: argparser object
     
    :rtpye: docker image with repo name
    generate_image_info(alg_info, container_name)
    generate wrapped image information for ecs task
     
    :para alg_info: algorthm information user provided
    :type: json
     
    :para container_name: access name of the wrapped container
    :type string
     
    rtype: json

__generate_runscript(input_path, output_path, name, command)__:
    generate runscript that fetch information from sqs, handling
    download/upload file and run script.
     
    :para input_path: input folder
    :type: string
     
    :para output_path: output folder
    :type: string
     
    :para name: new docker image name
    :type: string
     
    :para command: run command of user's algorithm script
    :type: string
     
    :return: the runscript for runscript.py. Include fetching information,
    download / upload file and run script.
    :rtype: string

__get_instance_type(alg_info)__:
    Based on the algorithm developer provided information, choose an
    apporperate ec2 instance_type
     
    :para alg_info: a json object contains necessory information about
    algorithm
    :type: json
     
    :rtype: sting of ec2 instance type
    show_dockerfile(system_name, container_name)
    show_runscript(input_path, output_path, name, command)
    wrapper(alg_info)
    automatic generate dockerfile according to the information user provided.
     
    :para alg_info: a json object contains necessory information about
    algorithm
    :type: json


### yunpipe.pipeline



### yunpipe.utils
Utility functions for yunpipe

__create_folder(folder)__:
    create folder if not existed

__get_full_path(path)__:
    convert a relative path to absolute path.

__get_int(message, default)__:
    transfer user input to int numbers. Continue asking unless valid input.
    If user omit the input and default is set to non-None, get default number
    instand.

    :para message: input message should to user
    :type: string

    :para default: default value

    :rtype: int

__get_true_or_false(message, default=False)__:
    transfer user input Y/n into True or False

    :para message: input message should to user
    :type: string

    :para default: default value

    :rtype: boolean


### yunpipe.script
command line scripts for yunpipe.

#### yunpipe.script.wrap
command line script for wrapping up user algorithm 

#### yunpipe.script.setup_pipe


