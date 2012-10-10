#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Mon 22 Aug 08:04:24 2011 

"""Runs the time analysis using a trained neural network and the protocol of
choice.
"""

import os
import sys
import bob
import argparse
from .. import ml
import ConfigParser

def write_table(title, analyzer, file, args):

  file.write( (len(title)+2) * '=' + '\n' )
  file.write( ' %s \n' % title )
  file.write( (len(title)+2) * '=' + '\n' )

  subtitle = '\nInstantaneous Analysis'
  file.write(subtitle + '\n')
  file.write(len(subtitle)*'-' + '\n\n')

  analyzer.write_table(file, instantaneous=True)
  
  prefix = 'Thresholded '
  if args.average: prefix = ''

  subtitle = prefix + 'Averaged Analysis'
  file.write('\n' + subtitle + '\n')
  file.write(len(subtitle)*'-' + '\n\n')
  
  analyzer.write_table(file, instantaneous=False)

def main():

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'scores')
  OUTPUTDIR = os.path.join(basedir, 'time-analysis')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('inputdir', metavar='DIR', type=str, nargs='?', default=INPUTDIR, help='directory containing the scores to be analyzed (defaults to "%(default)s").')
 
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results (defaults to "%(default)s").')

  parser.add_argument('-w', '--windowsize', metavar='INT', type=int,
      default=20, help='size of the window used when generating the input data - this variable is used to calculate the time variable for plots and tables (defaults to %(default)s)')

  parser.add_argument('-o', '--overlap', metavar='INT', type=int,
      default=0, help='size of the window overlap used when generating the input data - this variable is used to calculate the time variable for plots and tables (defaults to %(default)s)')

  parser.add_argument('-a', '--average', default=False, action='store_true',
      dest='average', help='if set, average thresholds instead of applying a score thresholding at every window interval')

  parser.add_argument('-m', '--min-hter', default=False, action='store_true',
      dest='minhter', help='if set, uses the min. HTER threshold instead of the EER threshold on the development set')

  parser.add_argument('-v', '--verbose', default=False, action='store_true',
      dest='verbose', help='increases the script verbosity')

  # Adds database support using the common infrastructure
  # N.B.: Only databases with 'video' support
  import antispoofing.utils.db 
  antispoofing.utils.db.Database.create_parser(parser, 'video')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory does not exist")

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory `%s'..." % args.outputdir
    bob.db.utils.makedirs_safe(args.outputdir)

  if args.overlap >= args.windowsize:
    parser.error("overlap has to be smaller than window-size")

  if args.overlap < 0:
    parser.error("overlap has to be 0 or greater")

  if args.windowsize <= 0:
    parser.error("window-size has to be greater than zero")

  db = args.cls(args)
  devel = dict(zip(('real', 'attack'), db.get_devel_data()))
  test = dict(zip(('real', 'attack'), db.get_test_data()))

  # make full paths
  devel['real'] = [k.make_path(args.inputdir, '.hdf5') for k in devel['real']]
  devel['attack'] = [k.make_path(args.inputdir, '.hdf5') for k in devel['attack']]
  test['real'] = [k.make_path(args.inputdir, '.hdf5') for k in test['real']]
  test['attack'] = [k.make_path(args.inputdir, '.hdf5') for k in test['attack']]

  # quickly load the development set and establish the threshold:
  thres = ml.time.eval_threshold(devel['real'], devel['attack'],
      args.minhter, args.verbose)

  analyzer = ml.time.Analyzer(test['real'], test['attack'], thres, 
      args.windowsize, args.overlap, args.average, args.verbose)

  outfile = os.path.join(args.inputdir, 'time-analysis-table.rst')

  title = 'Time Analysis, Window *%d*, Overlap *%d*' % (args.windowsize, args.overlap)

  write_table(title, analyzer, open(outfile, 'wt'), args)

  if args.verbose: write_table(title, analyzer, sys.stdout, args)

  outfile = os.path.join(args.inputdir,
      'time-analysis-misclassified-at-220.txt')
  analyzer.write_misclassified(open(outfile, 'wt'), 220) #Canonical limit

  outpdf = os.path.join(args.inputdir, 'time-analysis.pdf')
  analyzer.plot(outpdf, title)

if __name__ == '__main__':
  main()
