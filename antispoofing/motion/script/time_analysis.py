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
from ... import ml

def write_table(title, analyzer, file, args, protocol, support):

  file.write( (len(title)+2) * '=' + '\n' )
  file.write( ' %s \n' % title )
  file.write( (len(title)+2) * '=' + '\n' )
  file.write('\nInput directory\n  %s\n' % args.inputdir)
  file.write('\nFeat. directory\n  %s\n\n' % args.featdir)

  subtitle = 'Instantaneous Analysis'
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

  support_choices = ('hand', 'fixed', 'hand+fixed')

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  FEATURE_DIR = os.path.join(basedir, 'clustered')
  NETWORK_DIR = os.path.join(basedir, 'window_based')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('-n', '--network-dir', metavar='DIR', type=str,
      dest='inputdir', default=NETWORK_DIR, help='directory containing the files to be analyzed - this is the directory containing the mlp machine and the "dataset" link')

  parser.add_argument('-f', '--feature-dir', metavar='DIR', type=str,
      dest='featdir', default=FEATURE_DIR, help='directory containing the per-client features - if not given, guessed from the input directory')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str,
      default='hand+fixed', dest='support', help='if set, limit performance analysis to a specific support - if not given, guessed from the input directory')

  parser.add_argument('-w', '--windowsize', metavar='INT', type=int,
      default=20, help='size of the window used when generating the input data - this variable is used to calculate the time variable for plots and tables - if not given, guessed from the input directory')

  parser.add_argument('-o', '--overlap', metavar='INT', type=int,
      default=0, help='size of the window overlap used when generating the input data - this variable is used to calculate the time variable for plots and tables - if not given, guessed from the input directory')

  parser.add_argument('-a', '--average', default=False, action='store_true',
      dest='average', help='average thresholds instead of applying a score thresholding at every window interval')

  parser.add_argument('-m', '--min-hter', default=False, action='store_true',
      dest='minhter', help='uses the min. HTER threshold instead of the EER threshold on the development set')

  parser.add_argument('-v', '--verbose', default=False, action='store_true',
      dest='verbose', help='increases the script verbosity')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory does not exist")

  # try to guess if required:
  if args.featdir is None or \
      args.support is None or \
      args.windowsize is None or \
      args.overlap is None:
    guess(args)

  if args.overlap >= args.windowsize:
    parser.error("overlap has to be smaller than window-size")

  if args.overlap < 0:
    parser.error("overlap has to be 0 or greater")

  if args.windowsize <= 0:
    parser.error("window-size has to be greater than zero")

  support = args.support
  if args.support == 'hand+fixed': args.support = None

  db = bob.db.replay.Database()

  def get_files(args, group, cls):
    return db.files(args.featdir, extension='.hdf5', support=args.support,
        protocol='print', groups=(group,), cls=cls)

  # quickly load the development set and establish the threshold:
  thres = ml.time.eval_threshold(args.inputdir, 'print', args.support,
      args.minhter, args.verbose)

  # runs the analysis
  if args.verbose: print "Querying replay attack database..."
  test_real = get_files(args, 'test', 'real')
  test_attack = get_files(args, 'test', 'attack')

  machfile = os.path.join(args.inputdir, 'mlp.hdf5')

  analyzer = ml.time.Analyzer(test_real.values(), test_attack.values(),
      machfile, thres, args.windowsize, args.overlap,
      args.average, args.verbose)

  outfile = os.path.join(args.inputdir, 'time-analysis-table.rst')

  title = 'Time Analysis, Window *%d*, Overlap *%d*, Protocol *%s*, Support *%s*' % (args.windowsize, args.overlap, 'print', support)

  write_table(title, analyzer, open(outfile, 'wt'), args, 'print', support)

  if args.verbose: 
    write_table(title, analyzer, sys.stdout, args, 'print', support)

  outfile = os.path.join(args.inputdir,
      'time-analysis-misclassified-at-220.txt')
  analyzer.write_misclassified(open(outfile, 'wt'), 220) #Canonical limit

  outpdf = os.path.join(args.inputdir, 'time-analysis.pdf')
  analyzer.plot(outpdf, title)

if __name__ == '__main__':
  main()
