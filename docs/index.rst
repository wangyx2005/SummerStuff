.. cloud_pipe documentation master file, created by
   sphinx-quickstart on Tue Jul 26 15:15:43 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to cloud_pipe's documentation!
======================================
This is an automatic setup tool for setting up the data analysis pipeline on the Amazon Web Services (AWS). It provides an easy to deploy, use and scale your data analysis algorithm and work flow on the cloud as well as sharing between colleges and institutions. It is developed in Python 3 using boto, the AWS SDK for Python.

Now cloud_pipe is on Pypi, and it supports pip. To install cloud_pipe,
`pip install cloud_pipe`. The latest version is v0.0.3.dev. After install cloud_pipe:

To submit an algorithm or bring your analyze tool, use `wrap -d`. For more options, check: `wrap --help`

To run single algorithm or deploy you analytical work flow, use `setup-pipe -f your-workflow-json`. For more options, check: `setup-pipe --help`


General
=======
.. toctree::
   :maxdepth: 2

   general

Quick Start
===========

.. toctree::
   :maxdepth: 2

   quickstart


How it works
============
.. toctree::
   :maxdepth: 2

   howitworks


Demos
============
.. toctree::
   :maxdepth: 2



API References
==============
.. toctree::
   :maxdepth: 2

   api

Roadmap
============
.. toctree::
   :maxdepth: 2

   todo



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

