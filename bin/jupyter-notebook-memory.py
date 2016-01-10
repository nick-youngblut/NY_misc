#!/usr/bin/env python

"""
jupyter-notebook-memory.py: get memory for each jupyter notebook

Usage:
  jupyter-notebook-memory.py [options]
  jupyter-notebook-memory.py -h | --help
  jupyter-notebook-memory.py --version

Options:
  -u=<u>        Show notebooks for only one user.
  --ports=<p>   Port range to check (comma-separated). 
                [default: 5000,30000]
  --version     Show version.
  -h --help     Show this screen.

Description:
  Get a tab-delimited table of how much rss memory is used by each
  Jupyter notebook kernel. The ports with the `--ports` range will
  be checked for notebooks using any of those ports. This is needed
  to map the memory usage info on the kernel to the file name of the 
  notebook.
  
  To view a nicely formated version of the output table in bash:
  `jupyter-notebook-memory.py | column -t -s $'\\t' | less -S`

"""

from docopt import docopt
import sys
import os
import pwd
import psutil
import re
import string
import json
import urllib2
import pandas as pd



def nb_mem(user=None):
    # memory info from psutil.Process
    UID   = 1
    EUID  = 2
    regex = re.compile(r'.+kernel-(.+)\.json')

    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    
    df_mem = []
    for pid in pids:
        try:
            ret = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
        except IOError: # proc has already terminated
            continue
    
        # jupyter notebook processes
        if len(ret) > 0 and 'share/jupyter/runtime' in ret:
            # kernel
            kernel_ID = re.sub(regex, r'\1', ret)
            kernel_ID = filter(lambda x: x in string.printable, kernel_ID)
	        
            # memory
            process = psutil.Process(int(pid))
            mem = round(process.memory_info()[0] / float(1e9), 3)
	        
            # user name for pid
            for ln in open('/proc/{}/status'.format(int(pid))):
                if ln.startswith('Uid:'):
                    uid = int(ln.split()[UID])
                    uname = pwd.getpwuid(uid).pw_name
            
            if user is not None and uname != user:
                continue
            else:
                # user, pid, memory, proc_desc
                df_mem.append([uname, pid, mem, kernel_ID])

    df_mem = pd.DataFrame(df_mem)
    if df_mem.shape[0] == 0:
        sys.exit('No notebooks found!')
    df_mem.columns = ['user', 'pid', 'memory_GB', 'kernel_ID']
    return df_mem


def nb_port(ports):
    df_nb = []
    for port in xrange(ports[0],ports[1]+1):
        sessions = None
        try:
            url = 'http://127.0.0.1:{}/api/sessions'.format(port)
            sessions = json.load(urllib2.urlopen(url))
        except urllib2.URLError:
            sessions = None
	    
        if sessions:
            for sess in sessions:
                kernel_ID = str(sess['kernel']['id'])
                notebook_path = sess['notebook']['path']
                df_nb.append([port, kernel_ID, notebook_path])
	            
    df_nb = pd.DataFrame(df_nb)
    if df_nb.shape[0] == 0:
        sys.exit('No notebooks found!')
    df_nb.columns = ['port', 'kernel_ID', 'notebook_path']
    return df_nb


def main(user, ports):
    # making tables of notebook info
    df_mem = nb_mem(user=user)
    df_nb = nb_port(ports=ports)
    # joining tables
    df = pd.merge(df_nb, df_mem, on=['kernel_ID'], how='inner')
    df = df.sort(['memory_GB'], ascending=False)
    
    # reordering df
    df = df[['user', 'memory_GB', 'port', 'notebook_path', 'pid', 'kernel_ID']]

    # writing
    df.to_csv(sys.stdout, sep='\t', index=False)
    

if __name__ == '__main__':
    uargs = docopt(__doc__, version='0.1')
    ports = [int(x) for x in uargs['--ports'].split(',')]
    main(user = uargs['-u'], ports=ports)

