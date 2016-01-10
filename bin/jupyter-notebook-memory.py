#!/usr/bin/env python

"""
jupyter-notebook-memory.py: get memory for each jupyter notebook

Usage:
  jupyter-notebook-memory.py [options]
  jupyter-notebook-memory.py -h | --help
  jupyter-notebook-memory.py --version

Options:
  -u=<u>        Show notebooks for only one user.
  -n=<n>        Number of parallel processes.
                [default: 10]
  --ports=<p>   Port range to check (comma-separated). 
                [default: 1000,32000]
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

  Note: notebooks may be on ports >32000 (up to ~65000), 
  but this requests in odd url requests issues that take a lot longer.

"""

from docopt import docopt
import sys
import os
import pwd
import psutil
import re
import string
import json
import requests
from itertools import chain
import multiprocessing as mp
import signal
import errno
from functools import wraps
import numpy as np
import pandas as pd


class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


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


@timeout(2)
def _get_requests(port):
    try:
        url = 'http://127.0.0.1:{}/api/sessions'.format(port)
        reqs = requests.get(url)
    except requests.ConnectionError:
        reqs = None   
    return reqs


def _np_port(port):    
    try:
        reqs = _get_requests(port)
    except TimeoutError:
        sys.stderr.write('port {}: timeout\n'.format(port))
        reqs = None

    ret = []
    if reqs:
        try:
            reqs = json.loads(reqs.content)
        except (AttributeError, ValueError) as e:
            pass
        for req in reqs:
            kernel_ID = req['kernel']['id']
            notebook_path = req['notebook']['path']
            ret.append([port, kernel_ID, notebook_path])
    return ret


def nb_port(ports, nprocs=1):
    p = mp.Pool(processes=int(nprocs))
    df_nb = p.map(_np_port, range(ports[0],ports[1]+1))
    df_nb = chain.from_iterable(df_nb)
    df_nb = [x for x in df_nb if len(x) > 0]
    df_nb = pd.DataFrame(df_nb)
    if df_nb.shape[0] == 0:
        sys.exit('No notebooks found!')
    df_nb.columns = ['port', 'kernel_ID', 'notebook_path']
    return df_nb


def main(user, ports, nprocs=1):
    # making tables of notebook info
    df_mem = nb_mem(user=user)
    df_nb = nb_port(ports=ports, nprocs=nprocs)
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
    main(user=uargs['-u'], ports=ports, nprocs=uargs['-n'])

