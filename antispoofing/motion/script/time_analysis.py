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
import numpy
import argparse
from .. import ml

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

def get_parameters(f):

  scores = bob.io.load(f)
  good = scores[~numpy.isnan(scores)]
  lscores = list(scores)
  first_detection = lscores.index(good[0])
  second_detection = lscores.index(good[1])
  windowsize = first_detection + 1
  overlap = windowsize - (second_detection - first_detection)

  return windowsize, overlap

def main():

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'scores')
  OUTPUTDIR = os.path.join(basedir, 'time-analysis')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('inputdir', metavar='DIR', type=str, nargs='?', default=INPUTDIR, help='directory containing the scores to be analyzed (defaults to "%(default)s").')
 
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results (defaults to "%(default)s").')

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

  db = args.cls(args)
  devel = dict(zip(('real', 'attack'), db.get_devel_data()))
  test = dict(zip(('real', 'attack'), db.get_test_data()))

  # make full paths
  devel['real'] = [k.make_path(args.inputdir, '.hdf5') for k in devel['real']]
  devel['attack'] = [k.make_path(args.inputdir, '.hdf5') for k in devel['attack']]
  test['real'] = [k.make_path(args.inputdir, '.hdf5') for k in test['real']]
  test['attack'] = [k.make_path(args.inputdir, '.hdf5') for k in test['attack']]

  # finds out window-size and overlap
  args.windowsize, args.overlap = get_parameters(devel['real'][0])
  if args.verbose:
    print "Discovered parameters:"
    print " * window-size: %d" % args.windowsize
    print " * overlap    : %d" % args.overlap

  # try a match with the next file, just to make sure
  windowsize2, overlap2 = get_parameters(devel['real'][1])
  if args.windowsize != windowsize2 or args.overlap != overlap2:
    raise RuntimeError, "A possible misdetection of windowsize and overlap occurred between files '%s' and '%s'. The first detection showed a window-size/overlap of %d/%d while the second, %d/%d. You will have to edit this script and set these values by hand" % (devel['real'][0], devel['real'][1], args.windowsize, args.overlap, windowsize2, overlap2)

  # quickly load the development set and establish the threshold:
  thres = ml.time.eval_threshold(devel['real'], devel['attack'],
      args.minhter, args.verbose)

  analyzer = ml.time.Analyzer(test['real'], test['attack'], thres, 
      args.windowsize, args.overlap, args.average, args.verbose)

  outfile = os.path.join(args.outputdir, 'time-analysis-table.rst')

  title = 'Time Analysis, Window *%d*, Overlap *%d*' % (args.windowsize, args.overlap)

  write_table(title, analyzer, open(outfile, 'wt'), args)

  if args.verbose: write_table(title, analyzer, sys.stdout, args)

  outfile = os.path.join(args.outputdir, 'time-analysis-misclassified-at-220.txt')
  analyzer.write_misclassified(open(outfile, 'wt'), 219) #Canonical limit

  outpdf = os.path.join(args.outputdir, 'time-analysis.pdf')
  analyzer.plot(outpdf, title)

if __name__ == '__main__':
  main()
