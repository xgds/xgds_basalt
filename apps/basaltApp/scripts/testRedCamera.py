import os
import threading
import datetime


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def pingCamera():
    hostname = "10.10.24.75"
    response = os.system("ping -c 1 " + hostname)
    #and then check the response...
    if response == 0:
        print hostname, 'is up!'
    else:
        print hostname, 'is down!'
  
def pingBackpack():
    hostname = "10.10.24.31" # EV 1 backpack
    response = os.system("ping -c 1 " + hostname)
    #and then check the response...
    if response == 0:
        print hostname, 'is up!'
    else:
        print hostname, 'is down!'
  
def __main__():
    set_interval(pingCamera, 1)
    set_interval(pingBackpack, 1)
    
__main__()