#!/usr/bin/env python

"""rnammer_filt.py: Filter out low scoring rnammer hits

Usage:
  rnammer_filt.py [options] <fasta>
  rnammer_filt.py -h | --help
  rnammer_filt.py --version

Options:
  -             fasta provided via STDIN.
  -s=<score>    rnammer score [default: 0].
  -h --help     Show this screen.
  --version     Show version.
Arguments:
  <fasta>       fasta file name (If not given, read from STDIN)

"""

from docopt import docopt

if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')


import sys
from Bio import SeqIO


# loading fasta via STDIN & filter by score=
for seq_rec in SeqIO.parse(sys.stdin, "fasta"):
    desc = seq_rec.description.split(' /score=')
    if float(desc[1]) > float(args['-s']):
        print seq_rec.format('fasta')
