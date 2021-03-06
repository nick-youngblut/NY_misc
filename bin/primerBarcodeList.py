#!/usr/bin/env python

"""
primerBarcodeList.py: listing primer barcode combinations for dual indexed primers

Usage:
  primerBarcodeList.py [options]
  primerBarcodeList.py -h | --help
  primerBarcodeList.py --version

Options:
  -i=<i>       Excel file with barcodes. 
               [Default: data/indexed_primers/Kozich_DualIndex_V4_primers.xlsx]
  --list       List files in data/indexed_primers directory.
  --sql=<q>    Filter barcode table with an sql statement. 
               [Default: select * from df]
  --xlsx=<x>   Output as excel file. File written to '--xlsx' 
  -h --help    Show this screen.
  --version    Show version.

Description:
  Make a table of pairwise combinations of primers based on excel table
    of forward and reverse primers (dual-indexed Illumina primers).
  This is useful for a making an 'index' file associating primer indices
    with samples.
  By default, the input will be an excel file in the 'data'
    directory in the app directory structure.

  Sql statements can be used to filter the table to just certain barcode
  combinations.

  The ATGC content of each barcode pair (absolute counts & percent of length)
  will also be written. 
"""

# import 
from docopt import docopt
import sys,os
import re 
import string
from collections import Counter
import pandas as pd
import pandasql
from glob import glob


# functions
def wells96(n=96):
    """Get well_IDs for a 96-well plate. Returns a list of well IDs
    Args:
    n -- number of well IDs to return.
    """
    letters = list(string.uppercase)[:8] * 12
    nums = [x for x in range(13)[1:] for y in range(8)]
    well_IDs = [''.join([x,str(y)]) for (x,y) in zip(letters, nums)]

    return well_IDs[:n]


def sqlFilter(df, sql):
    """Filtering pandas dataframe using sql.
    Args:
    df -- dataframe object
    sql -- sql statement
    Return:
    dataframe object
    """
    df = pandasql.sqldf(sql, locals())

    # check selection
    err_msg = 'ERROR: No rows selected by --sql'
    try:
        df.shape
    except AttributeError:
        sys.exit(err_msg)
    if df.shape[0] == 0:
        sys.exit(err_msg)

    # return
    return df
        

def _ATGC_Counter(l):    
    c = Counter(l)
    return {x:c[x] for x in list('ATGC')}
    
def add_ATGC_counts(df):
    """Adding colums containing ATGC counts
    Args:
    df -- pandas dataframe
    """
    # adding counts
    barcodes = [x + y for (x,y) in zip(df.ix[:,'fwd_barcode'],
                                       df.ix[:,'rev_barcode'])]
    counts = [_ATGC_Counter(list(x)) for x in barcodes]
    df = pd.concat([df, pd.DataFrame(counts)], axis=1)
    # also adding percentages
    barcode_lens = [len(x) for x in barcodes]

    for let in list('ATGC'):
        df[let + '_perc'] = df[let] / barcode_lens * 100

    return df

    
def main(args):
    # list file
    if args['--list']:
        scriptDir = os.path.dirname(__file__)
        dataDir = os.path.join(scriptDir, '../data/indexed_primers/*.xls*')
        print '\n'.join(glob(dataDir))
        sys.exit()

    # reading in indexed primer file
    try:
        df = pd.read_excel(args['-i'])
    except IOError:
        scriptDir = os.path.dirname(__file__)
        dataDir = os.path.join(scriptDir, '../' + args['-i'])
        df = pd.read_excel(dataDir)
    df.columns = [x.upper() for x in df.columns]

    
    # IO assertions
    needed_cols = ['plate', 'primer_direction', 'count', 'index']
    needed_cols = [x.upper() for x in needed_cols]
    for col in needed_cols:
        assert col in df.columns, 'ERROR: column "{}" not found'.format(col)

    # well_IDs
    well_IDs = wells96()
                
    # making table of pairwise primer combinations
    res = pd.DataFrame(columns=['plate', 'well_ID', 
                                'location_16S_ID', 'ref_paper_ID',
                                'primerFR_ID_byPlate','primerFR_ID_total', 
                                'fwd_barcode', 'rev_barcode'])

    primerFR_ID_total = 0
    for plate in set(df.PLATE):
        df_fwd = df.loc[(df.PLATE == plate) & (df.PRIMER_DIRECTION == 'fwd')]
        df_rev = df.loc[(df.PLATE == plate) & (df.PRIMER_DIRECTION == 'rev')]
        primerFR_ID_byPlate = 0

        for i in xrange(df_rev.shape[0]):
            rev_barcode_row = df_rev.iloc[i]
            for ii in xrange(df_fwd.shape[0]):
                fwd_barcode_row = df_fwd.iloc[ii]
                
                primerFR_ID_total += 1
                primerFR_ID_byPlate += 1

                # getting IDs
                well_ID = well_IDs[primerFR_ID_byPlate-1]
                fwd_barcode = fwd_barcode_row.INDEX
                rev_barcode = rev_barcode_row.INDEX
                try:
                    fwd_16S_ID = fwd_barcode_row.LOCATION_16S_ID
                    rev_16S_ID = rev_barcode_row.LOCATION_16S_ID
                except AttributeError:
                    fwd_16S_ID = 'NA'
                    rev_16S_ID = 'NA'
                x16S_ID = '__'.join([fwd_16S_ID, rev_16S_ID])
                try:
                    fwd_paper_ID = fwd_barcode_row.REF_PAPER_ID
                    rev_paper_ID = rev_barcode_row.REF_PAPER_ID
                except AttributeError:
                    fwd_paper_ID = 'NA'
                    rev_paper_ID = 'NA'
                ref_paper_ID = '__'.join([fwd_paper_ID, rev_paper_ID])
                
                res.loc[primerFR_ID_total-1] = [plate, 
                                                well_ID,
                                                x16S_ID,
                                                ref_paper_ID,
                                                primerFR_ID_byPlate,
                                                primerFR_ID_total,
                                                fwd_barcode,
                                                rev_barcode]

    # table formatting
    res['plate'] = res['plate'].astype(int)
    res['primerFR_ID_byPlate'] = res['primerFR_ID_byPlate'].astype(int)
    res['primerFR_ID_total'] = res['primerFR_ID_total'].astype(int)
                
    # filtering via sql
    res = sqlFilter(res, args['--sql'])
    
    # adding A,T,G,C counts to table
    res = add_ATGC_counts(res)

    # table formatting (again)
    res['plate'] = res['plate'].astype(int)
    res['primerFR_ID_byPlate'] = res['primerFR_ID_byPlate'].astype(int)
    res['primerFR_ID_total'] = res['primerFR_ID_total'].astype(int)
    
    # output
    if args['--xlsx']:
        writer = pd.ExcelWriter(args['--xlsx'])
        res.to_excel(writer, 'primerFR_table')
        writer.save()
        sys.stderr.write('File written: {}\n'.format(args['--xlsx']))
    else:
        res.to_csv(sys.stdout, sep='\t', index=False)

    
if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')
    main(args)

