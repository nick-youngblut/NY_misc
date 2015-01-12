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

    letters = list(string.uppercase)[:8] * 12
    nums = [x for x in range(13)[1:] for y in range(8)]
    well_IDs = [''.join([x,str(y)]) for (x,y) in zip(letters, nums)]
    
    if args['--wide']:
        for x in xrange(8):
            print '\t'.join(well_IDs[x::8])
    else:    
        for i in xrange(int(args['-n'])-1):
            print well_IDs[i]

    


