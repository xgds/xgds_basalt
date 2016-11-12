#!/usr/bin/env python
import datetime
import os
import time
import memcache
import logging
import json
import dateutil.parser

import django
django.setup()

from xgds_status_board.models import Subsystem, SubsystemStatus


def setSubsystemStatus(opts):
    """
    Pings each subsystem for a response at every "interval_sec" seconds.
    """
    subsystemName = opts.subsystemName
    try: 
        subsystemStatus = SubsystemStatus(subsystemName)
    except:
        logging.error('invalid subsystem name')
        return 
    hostname = subsystemStatus.subsystem.getHostname()
    while hostname:
        status = subsystemStatus.getStatus()
        lastUpdated = dateutil.parser.parse(status['lastUpdated'])
        statusColor = subsystemStatus.getColorLevel(lastUpdated)
        elapsedTime = subsystemStatus.getElapsedTimeString(lastUpdated)
        status['statusColor'] = statusColor
        status['elapsedTime'] = elapsedTime

        seconds = subsystemStatus.subsystem.refreshRate
        logging.info('pinging %s' % opts.subsystemName)
        
        response = os.system("ping -c 1 " + hostname)
        if response != 0: # cannot ping host
            # try pinging again.
            response = os.system("ping -c 1 " + hostname)
        if response == 0: # hostname is up
            status['lastUpdated'] = datetime.datetime.utcnow().isoformat()
        subsystemStatus.setStatus(status)
        time.sleep(seconds)

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
