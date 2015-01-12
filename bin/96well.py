#!/usr/bin/env python

#--- Option parsing ---#
"""
96well: quick well_ID listing for 96-well plate

Usage:
  96well [options]
  96well -h | --help
  96well --version

Options:
  -n=<n>       Number of wells. [Default: 96]
  -w --wide    Wide plate format
  -h --help    Show this screen.
"""

from docopt import docopt
import sys,os
import string


if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')
    args['-n'] = int(args['-n'])

    letters = list(string.uppercase)[:8] * 12
    nums = [x for x in range(13)[1:] for y in range(8)]
    well_IDs = [''.join([x,str(y)]) for (x,y) in zip(letters, nums)]
    
    if args['--wide']:
        well_IDs = [well_IDs[i] if i <= args['-n'] else '' for i in xrange(len(well_IDs))]
        for x in xrange(8):
            print '\t'.join(well_IDs[x::8])
    else:    
        for i in xrange(args['-n']):
            print well_IDs[i]

    


