*****
Kytos End-2-End-Tests
*****

Overview
########

The purpose of this repository is to eventually house all the End-to-End code necessary to test the entirety of the Kytos SDN Controller.
As of today, the E2E code available analyzes the mef_eline, topology, and maintenance Napps, as well as it ensures the proper start of Kytos without errors.
All tests are based on simple Mininet topologies (which are provided in the helpers.py file), and they are executed within a docker container that holds the 
code for installing all the basic requirements needed to set up an environment capable of executing the tests.

Getting started
########

Once you have cloned this project, you need to go into the project repository and run the following command::

  $ docker-compose up

This will create and start services as outlined in your docker-compose.yml file, which in this case are to kickstart the installation of the docker images 
for Kytos and Mininet.

After all installations finish, the docker-compose file will call the kytos-init.sh script which takes care of finishing installing Kytos and all of the required 
network applications in a quick and efficient way. This script is also responsible for executing all the tests within the projects repository via the commands::

  $ python -m pytest --timeout=60 tests/ # Which runs all available tests

or::

  $ python -m pytest --timeout=60 tests/test_e2e_10_mef_eline.py::TestE2EMefEline::test_on_primary_path_fail_should_migrate_to_backup # Which only runs specific tests

The above lines are entirely up to the user to modify, and will allow them to choose in which way they want to use the tests.

Requirements
########

Python

Mininet

Docker

Kytos SDN Controller

Kytos/storehouse

Kytos/of_core 

Kytos/flow_manager 

Kytos/topology 

Kytos/of_lldp pathfinder 

Kytos/mef_eline 

Kytos/maintenance


