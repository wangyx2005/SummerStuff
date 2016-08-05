### For Algorithm Developers
Using this automatic tool for algorithm developers is very easy. 
All you need to do is to have your algorithm containerized and run `wrap`


#### Using command line editor
cloud_pipe offers an command line editor to describe your algorithm. Use `wrap --describe --show --user your-docker-account` or `wrap -ds -u your-docker-account`. A interactive command shell will pop up to help you describe your algorithm. For detailed explanation of each entry, check detailed explanation of algorithm entries section.

wrap.pic

After you finish describe your algorithm, a json file is showed to let you verify every thing is correct. 

json.pic

Once you confirm everything is correct, cloud_pipe will build a new image and upload to your docker hub account. Make sure you have already sign up and sign in you docker hub account.
At the same time, a more detailed json file describe your algorithm will be generated and stored in ~/.cloud_pipe/algorithms folder under your algorithm name for algorithm users to use locally. 

#### Use pre-prepared json file
cloud_pipe provides options using pre-prepared json file directly. use
```
wrap --files list-of-json-files --user your-docker-hub-account
```
cloud_pipe will build new images based on those files and upload to your docker hub account. At the same time, more detailed json files describe your algorithms will be generated and stored in ~/.cloud_pipe/algorithms folder under your algorithm name for algorithm users to use locally. 


##### Prepare your json file
If you prefer,  your algorithm json file directly. Here is an example of the json file describing the same algorithm in Using command line editor section.
```json
{
    "container_name": "wangyx2005/change123",
    "system": "ubuntu",
    "input_file_path": "/",
    "output_file_path": "/",
    "executable_path": "/change123",
    "run_command": "sh /change123.sh $input $output",
    "name": "change123-s3",
    "instance_type": "",
    "memory": 
    {
        "minimal": 50,
        "suggested": 128
    },
    "CPU": 1,
    "user_specified_environment_variables": 
    [
        {
            "name": "TEST_ENV",
            "required": true
        }
    ],
    "port": 
    [
        {
            "port": 9090,
            "protocol": "tcp"
        }
    ]
}
```

##### detailed explanation of algorithm entries:

- __container_name__: your containerized algorithm image. should be reachable from `docker pull`
- __system__: the system from which your image is built on. We currently support only ubuntu
- __run_command__: the command to run your algorithm. please substitute your input file with `$input`, output file/folder with `$output` and using the executable with the full path.
- __input_file_path__: the folder where input file should be
- __output_file_path__: the folder where output file should be
- __executable_path__: the full path of the executable
- __name__: A name which other algorithm user will refer this algorithm as. Need to be unique.

- __instance_type__: As algorithm developer, we believe you have a better understanding of your algorithm than anyone else. please suggest a instance type where this algorithm preferably running on on AWS.
- __memory__: the minimal and suggested memory requirement for running this algorithm container. You can omit minimal.
- __CPU__: the number of CPU used for using algorithm 
- __user_specified_environment_variables__: this is the list of variable you allow other algorithm user to use, such as seed. 
- __port__: the port number your algorithm exposed.



We will add a registry option to allow people upload images to other registries like amazon container registry.

Right now, sharing algorithm between users requires sharing corresponding json files in ~/.cloud_pipe/algorithms as well.
We are working on to set up a database to enable developers to save the algorithm json file remotely to make it easy for users to use their algorithms
