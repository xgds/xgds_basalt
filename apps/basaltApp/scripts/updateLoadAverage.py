#!/usr/bin/env python
import datetime
import os
import time
import memcache
import logging
import json
import re

import django
django.setup()

from xgds_status_board.models import Subsystem
_cache = memcache.Client(['127.0.0.1:11211'], debug=0)


def updateLoadAverage(opts):
    """ 
    updates the load average
    """
    import subprocess
    import sys

    while True: 
        myKey = ""
        if opts.serverName == "field":
            myKey =  'fieldLoadAverage'
            HOST = "irg@basalt-field"
        elif opts.serverName == "basecamp":  
            myKey = 'basecampLoadAverage'
            HOST = "irg@shore"
        else: 
            print "Please correctly type the name of the server (either 'field' or 'basecamp')"
            return 
        COMMAND="uptime"
    
        ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        
        result = ssh.stdout.readlines()
        if result !=[]:
            loadStr = re.search('load average:(.*)\n', result[0]).group(1)
            loadTimes = loadStr.split(",")
            oneMin = float(loadTimes[0].strip())
            fiveMin = float(loadTimes[1].strip())
            status = {"oneMin": oneMin,
                      "fiveMin": fiveMin,
                      "lastUpdated": datetime.datetime.utcnow().isoformat()}
            _cache.set(myKey, json.dumps(status))
        time.sleep(60)
    
 
def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-n', '--serverName',
                      default="field",
                      help='name of the server [field, basecamp]')
    opts, _args = parser.parse_args()
    updateLoadAverage(opts)


if __name__ == '__main__':
    main()