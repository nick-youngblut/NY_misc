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
    config = load_config(r'/home/nick/.pushbullet')
    try:
        api_key = config['nick']
    except KeyError:
        raise KeyError, '"nick" API key not found in config file'
        
    pb = Pushbullet(api_key)
    push = pb.push_note(msg, '')

    
def load_ipython_extension(ipython):
    ipython.register_magic_function(pushnote, 'line')




class Pushnote_OLD(object):
    """Class that provides a pushbullet notification if the cell took 
    a while to finish.
    """

    def __init__(self):
        print(os.path.abspath(os.path.curdir))
        self.start_time = 0.0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time:
            diff_time = time.time() - self.start_time
            assert diff_time > 0
            #print('time: %s' % format_delta(diff))
            if diff_time > 180:
                self.pushnote(diff_time)

    def load_config(self, configFile):
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
	
    def pushnote(self, diff_time):
        config = self.load_config(r'/home/nick/.pushbullet')
        try:
            api_key = config['api_key']
        except KeyError:
            sys.exit('"api_key" not found in config file')

        pb = Pushbullet(api_key)
        msg = 'Cell completed in {0:.3f} secs'.format(diff_time)
        push = pb.push_note(msg, '')
	

#PN = Pushnote()

#def load_ipython_extension(ip):
#    ip.events.register('pre_run_cell', PN.start)
#    ip.events.register('post_run_cell', PN.stop)


#def unload_ipython_extension(ip):
#    ip.events.unregister('pre_run_cell', PN.start)
#    ip.events.unregister('post_run_cell', PN.stop)
