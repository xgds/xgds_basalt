#! /bin/bash

# Restores a copy of the unmodified tungsten replicator service properties files
# so the tpm command does not die.  It does not play well with customized
# property file (e.g. local javascript filters).

rm ~/tungsten/releases/tungsten-replicator-oss-4.0.1-123_pid[0-9]*/tungsten-replicator/conf/static-[A-Z,a-z]*.properties

rsync -auv ~/replicator-properties/orig/* ~/tungsten/releases/tungsten-replicator-oss-4.0.1-123_pid[0-9]*/tungsten-replicator/conf
