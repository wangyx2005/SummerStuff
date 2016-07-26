This is an automatic setup tool for setting up the data analysis pipeline on the AWS. It provides utility functions to facilitate algorithm developer to build their analytical tools in docker container, published them for others to use and users to use those analytical tools to facilitate their analysis.

Currently we only support us-east-1 region. We will support other regions in the near future

The __container_wrapper__ folder contains all the utility functions for algorithm developers and __setup__ folder is for user to submit their analytical workflows.

Once new algorithm has been added, __algorithms__ folder will be created to save the detailed information about the algorithm.