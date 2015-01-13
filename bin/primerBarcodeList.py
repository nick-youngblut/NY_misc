[B#!/usr/bin/env python

"""
primerBarcodeList.py: listing primer barcode combinations for dual indexed primers

Us0;95;cage:
  primerBarcodeList.py [options]
  primerBarcodeList.py -h | --help
  primerBarcodeList.py --version

Options:
  -i=<i>       Excel file with barcodes. Default=data/indexed_primers/ndexed_V4-V5_primers_db.xlsx
  --xlsx=<x>   Output as excel file. File written to '--xlsx' 
  -h --help    Show this screen.
  --version    Show version.

Description:
  Make a table of pairwise combinations of primers based on excel table of forward
  and reverse primers (dual-indexed Illumina primers).
  This is useful for a making an 'index' file associating primer indices with samples.
  By default, the input will be an excel file in the 'data' directory in the app directory structure.
"""

from docopt import docopt
import sys,os
import pandas as pd
import re 
import string

scriptDir = os.path.dirname(__file__)
dataDir = os.path.join(scriptDir, '../data/indexed_primers/indexed_V4-V5_primers_db.xlsx')


def wells96(n=96):
    """Get well_IDs for a 96-well plate. Returns a list of well IDs
    Args:
    n -- number of well IDs to return.
    """
    letters = list(string.uppercase)[:8] * 12
    nums = [x for x in range(13)[1:] for y in range(8)]
    well_IDs = [''.join([x,str(y)]) for (x,y) in zip(letters, nums)]

    return well_IDs[:n]
    
                
def main(args):
    # input
    if not args['-i']:
        args['-i'] = dataDir
    df = pd.read_excel(args['-i'])
    df.columns = [x.upper() for x in df.columns]
    
    # IO assertions
    needed_cols = [x.upper() for x in ['plate', 'primer_direction', 'count', 'index']]
    for col in needed_cols:
        assert col in df.columns, 'ERROR: column "{}" not found'.format(col)

    # well_IDs
    well_IDs = wells96()
                
    # making table of pairwise primer combinations
    res = pd.DataFrame(columns=['plate', 'well_ID', 'primerFR_ID_byPlate',
                                'primerFR_ID_total', 'fwd_barcode', 'rev_barcode'])
    primerFR_ID_total = 0
    for plate in set(df.PLATE):
        df_fwd = df.loc[(df.PLATE == plate) & (df.PRIMER_DIRECTION == 'fwd')]
        df_rev = df.loc[(df.PLATE == plate) & (df.PRIMER_DIRECTION == 'rev')]
        primerFR_ID_byPlate = 0

        for i in xrange(df_rev.shape[0]):
            rev_barcode_row = df_rev.iloc[i]
            for ii in xrange(df_fwd.shape[0]):
                fwd_barcode_row = df_fwd.iloc[ii]

                #print '{}\t{}'.format(fwd_barcode_row.INDEX, rev_barcode_row.INDEX)
                
                primerFR_ID_total += 1
                primerFR_ID_byPlate += 1
                well_ID = well_IDs[primerFR_ID_byPlate-1]
                fwd_barcode = fwd_barcode_row.INDEX
                rev_barcode = rev_barcode_row.INDEX
                
                res.loc[primerFR_ID_total-1] = [plate, well_ID,
                                                primerFR_ID_byPlate,
                                                primerFR_ID_total,
                                                fwd_barcode,
                                                rev_barcode]

    # table edit
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

