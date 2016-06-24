#!/usr/bin/env python
import datetime
import os
import time
import memcache
import logging
import json

import django
django.setup()

from xgds_status_board.models import Subsystem
_cache = memcache.Client(['127.0.0.1:11211'], debug=0)
    
        
def setSubsystemStatus(opts):
    """
    Pings each subsystem for a response at every "interval_sec" seconds.
    """
    while True:
        time.sleep(5)
        logging.info('pinging %s' % opts.subsystemName)
        subsystemName = opts.subsystemName
        try: 
            subsystem = Subsystem.objects.get(name=subsystemName)
        except: 
            logging.error('cannot get IP of %s' % subsystemName)
            continue
        hostname = subsystem.getHostname()
        response = os.system("ping -c 1 " + hostname)
        if response != 0: # cannot ping host
            # try pinging again.
            response = os.system("ping -c 1 " + hostname)
        if response == 0: # hostname is up
            myKey = subsystemName
            status = {"lastUpdated": datetime.datetime.utcnow().isoformat()}
            _cache.set(myKey, json.dumps(status))
        

def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-n', '--subsystemName',
                      default="",
                      help='name of the subsystem to ping')
    opts, _args = parser.parse_args()
    setSubsystemStatus(opts)


if __name__ == '__main__':
    main()
