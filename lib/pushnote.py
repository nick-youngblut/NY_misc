#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import re
import time
from IPython.core.magics.execution import _format_time as format_delta

from pushbullet import Pushbullet


def load_config(configFile):
    configFile = os.path.expanduser(configFile)
    config = {}
    with open(configFile, 'rb') as inFH:
        for line in inFH:
            line = line.rstrip()
            if len(line) == 0:
                continue
            x = re.split('\s*[,=]\s*', line)
            config[x[0].lower()] = x[1]
    return config
	

def pushnote(msg):
    homeDir =  os.path.expanduser('~')
    configFile = os.path.join(homeDir, '.pushbullet')
    config = load_config(configFile)
    try:
        api_key = config['pushnote']
    except KeyError:
        msg = '"pushnote" API key not found in config file: {}'
        raise KeyError, msg.format(configFile)
        
    pb = Pushbullet(api_key)
    push = pb.push_note(msg, '')

    
def load_ipython_extension(ipython):
    ipython.register_magic_function(pushnote, 'line')



if __name__ == '__main__':
    msg = """
To install: 
    First, make a config file with the PushBullet API key.
    1) Make a file in your home directory called .pushpullet 
    2) In the file add the API key
      *) You can have muliple API keys for difference purposes
      *) For the API key you want to use for pushnote, use the format:
         `pushnote = o.ExVQMadIvsjVca134dajA131dDK`
      *) Note: after the equals is the API key. 
      *) Just to be clear, there should be a line in the config file that looks
         something like this `pushnote = o.ExVQMadIvsjVca134dajA131dDK`
    
    To install the extension:
      In Jupyter/Ipython: `%install_ext pushnote.py`

To use:
    `%pushnote This is a test message`
"""
    print(msg)

