#! /bin/bash

# Dynamically edit properties file to include our local JS filter(s)

ansible-playbook installReplicationJsScripts.yml -c local --inventory-file="localhost,"
