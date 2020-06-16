#!/bin/bash

apt-get update -y && apt-get upgrade -y

pip install --upgrade pip setuptools wheel

for i in python-openflow kytos-utils kytos storehouse of_core flow_manager topology of_lldp pathfinder; do
	git clone https://github.com/kytos/$i; 
	cd $i; 
	pip install -r requirements/dev.txt; 
	python setup.py develop; 
	cd ..; 
done

kytosd -f
