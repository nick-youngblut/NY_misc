#!/usr/bin/env python

#--- Option parsing ---#
"""
geo_coord_convert.py: converting geolocation coordinates to decimal degrees

Usage:
  geo_coord_convert.py [options]
  geo_coord_convert.py [options] < pipe
  geo_coord_convert.py -h | --help
  geo_coord_convert.py --version

Options:
  -d <d>        Value delimiter. [default: \t]
  -l <l>        Line terminator (interactive mode). [default: ;]
  -i <i>        Input format. [default: DDM]
  -h --help     Show this screen.
  --version     Show version.

Description:
  Can convert lat-long values from Degrees Decimal Minutes (DDM)
  or Degrees Minutes Seconds (DMS) to Decimal Degrees (DD).
Examples of value types:
  DDM = '76 58.747 N' or  '42 41.718 W'
  DMS = '40° 45' 36.000" N' or '73° 59' 2.400"'
  DD = '76.5814123' or '-42.411312'
"""

from docopt import docopt
import sys
import os
from StringIO import StringIO
import re

import pandas as pd
import geopy

scriptDir = os.path.dirname(__file__)
libDir = os.path.join(scriptDir, '../lib/')
sys.path.append(libDir)

import Geo

#-- functions
def DDM2DD(string, hemi=None):
    """Convert from degrees decimal minutes to decimal degrees.

    Args:
    string -- string of coordinate
    lat_long -- either 'lat' or 'long'
    hemi -- hemisphere for lat/long (if not provided in string)
    """

    string = str(string)
    
    # parsing
    ret = re.search('(\d+) +([0-9.]*) *([NSEWnsew]*)', string)
    try:
        groups = list(ret.groups())
    except:
        raise TypeError('{} is in the wrong format.\n'.format(string))

    # degrees            
    try:
        groups[0] = float(groups[0])
    except NameError as err:
        raise type(err)(err.message + '. "{}" must include degrees\n'.format(row[0]))
    ## min to DD
    try:
        groups[1] = float(groups[1])
    except NameError:
        groups[1] = 0

    # DD
    DD = groups[0] + float(groups[1] / 60)
    
    # lat-long
    try:
        hemi = groups[2].upper()
    except NameError:
        try:
            hemi = hemi.upper()
        except NameError as err:
            raise type(err)(err.message + '. "{}" does not contain hemisphere.\n'.format(string))
    if hemi == 'S' or hemi == 'W':
        DD = -DD
        
    return DD

def DMS2DD(string, hemi=None):
    """Convert from degrees minutes seconds to decimal degrees.

    Args:
    string -- string of coordinate
    lat_long -- either 'lat' or 'long'
    hemi -- hemisphere for lat/long (if not provided in string)
    """

    string = str(string)

    # strip unicode
    string = string.decode('unicode_escape').encode('ascii','ignore')
    
    # parsing
    ret = re.search('(\d+)\D+(\d*)\D*(\d*) *([NSEWnsew]*)', string)
    try:
        groups = list(ret.groups())
    except:
        raise TypeError('{} is in the wrong format.\n'.format(string))

    # degrees            
    try:
        groups[0] = float(groups[0])
    except NameError as err:
        raise type(err)(err.message + '. "{}" must include degrees\n'.format(row[0]))
    ## min to DD
    try:
        groups[1] = float(groups[1])
    except NameError:
        groups[1] = 0

    ## sec to DD
    try:
        groups[2] = float(groups[2])
    except NameError:
        groups[2] = 0

    # DD
    DD = groups[0] + float(groups[1] / 60) + float(groups[2] / 3600)
    
    # lat-long
    try:
        hemi = groups[3].upper()
    except NameError:
        try:
            hemi = hemi.upper()
        except NameError as err:
            raise type(err)(err.message + '. "{}" does not contain hemisphere.\n'.format(string))
    if hemi == 'S' or hemi == 'W':
        DD = -DD

    return DD
        

#-- main
if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')
    
    # input
    ## interactive
    if sys.stdin.isatty():
        inString = raw_input('Provde coordinates (semi-colon delimited)\n')
        df = pd.read_csv(StringIO(inString), header=None, lineterminator=args['-l'], sep=args['-d'])        
    ## stdin
    else:
        pd.read_csv(sys.stdin, header=None, sep=args['-d'])
        
    # checking df
    if df.shape[1] < 2:
        raise IOError('The provided table must have 2 columns (lat, long)\n')

    # Converting
    ## TODO: add more conversion methods & doc
    if args['-i'].upper() == 'DDM':
        df = df.applymap(DDM2DD)
    elif args['-i'].upper() == 'DMS':
        df = df.applymap(DMS2DD)

    # writing
    df.to_csv(sys.stdout, header=False, index=False, sep='\t')
        