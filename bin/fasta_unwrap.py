#!/usr/bin/env python

"""
fasta_unwrap.py: hard-wrapped fastas unwrapped (sequence is just 1 line)

Usage:
  fasta_unwrap.py <fasta> | [-]
  fasta_unwrap.py -h | --help
  fasta_unwrap.py --version

Options:
  -             Fasta from STDIN
  -h --help     Show this screen.
  --version     Show version.
  --drifting    Drifting mine.
Arguments:
  <fasta>       fasta file name (STDIN if not given)
"""

from docopt import docopt

if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')

import sys
import fileinput
import re

# IO error
if args['<fasta>'] is None:
    sys.stderr.write('Provide fasta via arg or STDIN')
    sys.stderr.write(__doc__)
    sys.exit()



if args['<fasta>'] == '-':
    inf = sys.stdin
else: 
    inf = open(args['<fasta>'], 'r')


# parsing fasta
fasta = dict()
tmpkey = ''
for line in inf:
    print line.rstrip()
