#!/usr/bin/env python
import datetime
import os
import time
import logging
import json
import re

import django
django.setup()

from xgds_status_board.models import Subsystem, SubsystemStatus


def updateLoadAverage(opts):
    """ 
    updates the load average
    """
    logging.info("Running %s" % opts.subsystemName)
    subsystemName = opts.subsystemName
    if subsystemName == "fieldLoadAverage":
        HOST = "irg@boat"
    elif subsystemName == "basecampLoadAverage":  
        HOST = "irg@shore"
    else: 
        print "Please correctly type the name of the server (either 'field' or 'basecamp')"
        return 
    COMMAND="uptime"
    logging.info('Saving load average info for %s' % subsystemName)
    try: 
        subsystemStatus = SubsystemStatus(subsystemName)
    except:
        logging.error('Error, invalid subsystem name: %s' % subsystemName)
        return
    while True: 
        result = subsystemStatus.runRemoteCommand(HOST, COMMAND)
        if result !=[]:
            loadStr = re.search('load average:(.*)\n', result[0]).group(1)
            loadTimes = loadStr.split(",")
            oneMin = float(loadTimes[0].strip())
            fiveMin = float(loadTimes[1].strip())
            lastUpdated = datetime.datetime.utcnow().isoformat()
            status = subsystemStatus.getStatus()
            status['oneMin'] = oneMin
            status['fiveMin'] = fiveMin
            status['lastUpdated'] = lastUpdated
            subsystemStatus.setStatus(status)
        else: 
            logging.error("Command %s in host %s returned []" % (COMMAND, HOST))
        time.sleep(60)
 
def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-n', '--subsystemName',
                      default="fieldLoadAverage",
                      help='fieldLoadAverage or basecampLoadAverage')
    opts, _args = parser.parse_args()
    updateLoadAverage(opts)


if __name__ == '__main__':
    main()