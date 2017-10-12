#!/usr/bin/env python

import optparse
from os import system

class ReplicationData:
    tableList = [{'database':'xgds_basalt',
                  'tables':[
                      'xgds_video_videosegment',
                      'xgds_video_videoepisode',
                      'xgds_core_constant',
                      'django_migrations',
                      'django_session',
                      'xgds_status_board_subsystem',
                      'xgds_status_board_subsystemgroup',
                      'xgds_core_relayevent',
                      'xgds_core_relayfile',
                      'basaltApp_basaltactiveflight'
                  ]}]

    remoteHostname = "boat"
    localHostname = "shore"

    replicationCommandBaseNoDelay = "/home/irg/tungsten/tungsten/tools/tpm update --hosts=%s,%s --repl-svc-applier-filters=replicate --property=replicator.filter.replicate.ignore="
    replicationCommandBaseWithDelay = "/home/irg/tungsten/tungsten/tools/tpm update --hosts=%s,%s --repl-svc-applier-filters=delay,replicate --property=replicator.filter.delay.delay=%s --property=replicator.filter.replicate.ignore="

    def getTableCommandString(self):
        tableStringList = []
        for ti in self.tableList:
            dbName = ti['database']
            for tname in ti['tables']:
                tableStringList.append("%s.%s" % (dbName, tname))

        tableCommandString = ",".join(tableStringList)
        return tableCommandString

    def buildReplicationCommand(self, delayTimeSecs=0, remoteHost=None):
        if remoteHost:
            if delayTimeSecs == 0:
                replicationCommand = self.replicationCommandBaseNoDelay % (self.localHostname, self.remoteHostname)
                cmdString = "ssh %s %s%s" % (self.remoteHostname, replicationCommand, self.getTableCommandString())
            else:
                replicationCommand = self.replicationCommandBaseWithDelay % (self.localHostname, self.remoteHostname, delayTimeSecs)
                cmdString = "ssh %s %s%s" % (self.remoteHostname, replicationCommand, self.getTableCommandString())
        else:
            if delayTimeSecs == 0:
                replicationCommand = self.replicationCommandBaseNoDelay % (self.localHostname, self.remoteHostname)
                cmdString = "%s%s" % (replicationCommand, self.getTableCommandString())
            else:
                replicationCommand = self.replicationCommandBaseWithDelay % (self.localHostname, self.remoteHostname, delayTimeSecs)
                cmdString = "ssh %s %s%s" % (self.remoteHostname, replicationCommand, self.getTableCommandString())
        return cmdString


def setReplicationTimeDelay(delayTime):
    print "Setting replication delay to %d seconds." % delayTime
    rd = ReplicationData()
    localCmd = rd.buildReplicationCommand(delayTime)
    remoteCmd = rd.buildReplicationCommand(delayTime, rd.remoteHostname)

    print "Running local filter command:"
    print localCmd
    print ""
    system(localCmd)

    print "Remote remote filter command:"
    print remoteCmd
    system(remoteCmd)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog -d <seconds>')
    parser.add_option('-d', '--delay',
                      default="0",
                      help='replication time delay in mm:ss or seconds')
    opts, _args = parser.parse_args()
    try:
        if ":" in opts.delay:
            min,sec = opts.delay.split(":")
            delayTime = 60*int(min) + int(sec)
        else:
            delayTime = int(opts.delay)
    except:
        print "Replication delay must be a valid pair of integer numbers (mins:seconds) or just seconds"
        exit(1)

    setReplicationTimeDelay(delayTime)


if __name__ == '__main__':
    main()
