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
from xbob.db.replay import Database
import ConfigParser

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

  db = Database()

  protocols = db.protocols()

  support_choices = ('hand', 'fixed', 'hand+fixed')

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  NETWORK_DIR = os.path.join(basedir, 'mlp')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('inputdir', metavar='DIR', type=str, nargs='?',
      default=NETWORK_DIR, help='directory containing the files to be analyzed - this is the directory containing the mlp machine')

  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str, choices=protocols, dest="protocol", help='The protocol type may be specified to subselect a smaller number of files to operate on (one of "%s") - if not given, it is read from the network directory file called "session.txt"' % '|'.join(sorted(protocols)))

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str, dest='support', help='if set, limit performance analysis to a specific support - if not given, it is read from the network directory file called "session.txt"')

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

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory does not exist")

  config = ConfigParser.SafeConfigParser()
  config.readfp(open(os.path.join(args.inputdir, "session.txt"), 'rb'))

  if args.protocol is None:
    args.protocol = config.get('mlp', 'protocol')

  if args.support is None:
    args.support = config.get('mlp', 'support').split()
  elif args.support == 'hand+fixed':
    args.support = args.support.split('+')

  if args.overlap >= args.windowsize:
    parser.error("overlap has to be smaller than window-size")

  if args.overlap < 0:
    parser.error("overlap has to be 0 or greater")

  if args.windowsize <= 0:
    parser.error("window-size has to be greater than zero")

  args.featdir = config.get('data', 'input')

  machfile = os.path.join(args.inputdir, 'mlp.hdf5')

  def get_files(args, group, cls):
    return db.files(args.featdir, extension='.hdf5', support=args.support,
        protocol=args.protocol, groups=(group,), cls=cls)

  # quickly load the development set and establish the threshold:
  thres = ml.time.eval_threshold(machfile, args.featdir, args.protocol, args.support,
      args.minhter, args.verbose)

  # runs the analysis
  if args.verbose: print "Querying replay attack database..."
  test_real = get_files(args, 'test', 'real')
  test_attack = get_files(args, 'test', 'attack')

  analyzer = ml.time.Analyzer(test_real.values(), test_attack.values(),
      machfile, thres, args.windowsize, args.overlap,
      args.average, args.verbose)

  outfile = os.path.join(args.inputdir, 'time-analysis-table.rst')

  title = 'Time Analysis, Window *%d*, Overlap *%d*, Protocol *%s*, Support *%s*' % (args.windowsize, args.overlap, args.protocol, args.support)

  write_table(title, analyzer, open(outfile, 'wt'), args, args.protocol, args.support)

  if args.verbose: 
    write_table(title, analyzer, sys.stdout, args, args.protocol, args.support)

  outfile = os.path.join(args.inputdir,
      'time-analysis-misclassified-at-220.txt')
  analyzer.write_misclassified(open(outfile, 'wt'), 220) #Canonical limit

  outpdf = os.path.join(args.inputdir, 'time-analysis.pdf')
  analyzer.plot(outpdf, title)

if __name__ == '__main__':
  main()
