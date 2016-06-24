#!/usr/bin/env python
import time
import requests  # pip install requests
import logging


def autorunPhotoImportScript(opts):
    sleepSeconds = 120
    timeoutSeconds = 20
    while True:
        scriptUrl = 'http://%s/fileUpdate.lua' % opts.hostname
        r = requests.get(scriptUrl, timeout=timeoutSeconds)
        logging.info(r.text)
        time.sleep(sleepSeconds)
        

def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-n', '--hostname',
                      default="",
                      help='name of the subsystem to ping')
    opts, _args = parser.parse_args()
    autorunPhotoImportScript(opts)


if __name__ == '__main__':
    main()