#! /bin/bash

# Saves a copy of the unmodified tungsten replicator service properties files
# so the tpm command does not die.  It does not play well with customized
# property file (e.g. local javascript filters).

rsync -auv ~/tungsten/releases/tungsten-replicator-oss-4.0.1-123_pid[0-9]*/tungsten-replicator/conf/static-[A-Z,a-z]*.properties ~/replicator-properties/orig
