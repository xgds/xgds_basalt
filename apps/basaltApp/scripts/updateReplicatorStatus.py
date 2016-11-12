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


def setReplicatorStatus(opts):
    """
    Pings each subsystem for a response at every "interval_sec" seconds.
    """
    subsystemName = opts.subsystemName
    try: 
        subsystemStatus = SubsystemStatus(subsystemName)
    except:
        logging.error('invalid subsystem name')
        return 
    if "boat" in subsystemName: 
        HOST = "irg@boat"
    elif "shore" in subsystemName:
        HOST = "irg@shore"
    else: 
        print "invalid subsystem name. Name must contain 'boat' or 'shore'"
        return 
    COMMAND = "/home/irg/tungsten/tungsten/tungsten-replicator/bin/trepctl services"
    
    while True: 
        result = subsystemStatus.runRemoteCommand(HOST, COMMAND)
        statusColor = subsystemStatus.OKAY
        if result !=[]:
            for line in result:
                if "state" in line: 
                    state = line.replace(" ", "").split(':')[1]
                    if "ONLINE" in state:
                        statusColor = subsystemStatus.ERROR
                        break
        else: # result is empty
            statusColor = subsystemStatus.NO_DATA

        status = subsystemStatus.getStatus()
        lastUpdated = status['lastUpdated']
        elapsedTimeString = subsystemStatus.getElapsedTimeString(lastUpdated)
        status['statusColor'] = statusColor
        status['elapsedTime'] = elapsedTimeString
        status['lastUpdated'] = datetime.datetime.utcnow().isoformat()
        subsystemStatus.setStatus(status)
        seconds = subsystemStatus.subsystem.refreshRate
        time.sleep(seconds)

def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-n', '--subsystemName',
                      default="",
                      help='name of the subsystem to ping')
    opts, _args = parser.parse_args()
    setReplicatorStatus(opts)


if __name__ == '__main__':
    main()
