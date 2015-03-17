#!/usr/bin/env python

"""
seqIntersect.py: Getting the intersection of 2 read files (just same reads in both).

Usage:
  seqIntersect.py [options] <read1> <read2>
  seqIntersect.py -h | --help
  seqIntersect.py --version

Options:
  <read1>        Read1 file (fastq, fasta, or screedDB).
  <read2>        Read2 file (fastq, fasta, or screedDB).
  -k --keep      Keep the created screed databases (if fastq or fasta files).
  -v --verbose   Verbose output.
  --version      Show version.
  -h --help      Show this screen.

Description:
  Intersection based on read names.

  The read files can be fastq or fasta formatted sequence files,
  or they can be screed databases (file names must end in '_screed').

  The sequences from <read1> are written to STDOUT.
"""

from docopt import docopt
import sys,os
from itertools import imap
import screed
import logging


def openDB(fileName):
    """Opening screed DB; making if not already existing
    Args:
    fileName -- Name of sequence file or screedDB file
    """
    logging.info('Making/opening screed database for: "{}"'.format(fileName))
    
    # making db if needed
    if not fileName.endswith('_screed'):
        try:
            screed.read_fastq_sequences(fileName)
            fileName = fileName + '_screed'
        except KeyError:
            try:
                screed.read_fasta_sequences(fileName)
                fileName = fileName + '_screed'
            except IOError:
                msg = 'Cannot open {}'.format(fileName)
                raise IOError(msg)

    # init screed db
    return screed.ScreedDB(fileName)

    
def get_screed_key_intersect(screed1, screed2):
    logging.info('Finding sequence intersection')
   
    for x in reduce(set.intersection, imap(set, [screed1.keys(), screed2.keys()])):
        seq = screed1[x]
        try:
            print '@{} {}\n{}\n+\n{}'.format(seq['name'], seq['annotations'],                                      
                                         seq['sequence'],
                                         seq['accuracy'])
        except KeyError:
            print '>{} {}\n{}'.format(seq['name'], seq['description'], seq['sequence'])

    
def rm_screed_db(fileName):
    """Delete the screed database file associated with the
    provided file. Associated Screed database assumeded
    to be 'fileName' + '_screed'.
    Args:
    fileName -- name of file that has an associated '*_screed' file
    """

    screedName = fileName + '_screed'
    if os.path.isfile(screedName):
        os.unlink(screedName)

    logging.info('Removed screed db file: "{}"'.format(screedName))


def main(uargs):
    if uargs['--verbose']:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    
    # init screed DB objects
    db_r1 = openDB(uargs['<read1>'])
    db_r2 = openDB(uargs['<read2>'])


    # intersection of read names
    get_screed_key_intersect(db_r1, db_r2)
                

    # delete screed files
    if not uargs['--keep']:
        rm_screed_db(uargs['<read1>'])
        rm_screed_db(uargs['<read2>'])
        
    

if __name__ == '__main__':
    uargs = docopt(__doc__, version='0.1')
    main(uargs)

