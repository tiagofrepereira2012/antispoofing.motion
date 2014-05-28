#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 02 Aug 2010 11:31:31 CEST 

"""Calculates the clustered values as described at the paper:
Counter-Measures to Photo Attacks in Face Recognition: a public database and a
baseline, Anjos & Marcel, IJCB'11.

This script will output a number of clustered observations containing the 5
described quantities for windows of a configurable size (N):

1. The minimum value observed on the cluster
2. The maximum value observed on the cluster
3. The mean value observed
4. The standard deviation on the cluster
5. The DC ratio (D) as defined by:

.. math::

  D(N) = \frac{\sum_{i=1}^N{|FFT_i|}}{|FFT_0|}
"""

import os, sys
import argparse

def main():

  import bob
  import numpy

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'framediff')
  OUTPUTDIR = os.path.join(basedir, 'clustered')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the frame differences to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR,
      nargs='?', help='Base output directory for every file created by this procedure (defaults to "%(default)s")')
  parser.add_argument('-n', '--window-size', dest="window_size", default=20,
      type=int, help="determines the window size to be used when clustering frame-difference observations (defaults to %(default)s)"),
  parser.add_argument('-o', '--overlap', dest="overlap", default=0, type=int,
      help="determines the window overlapping; this number has to be between 0 (no overlapping) and 'window-size'-1 (defaults to %(default)s)"),

  # The next option just returns the total number of cases we will be running
  # It can be used to set jman --array option. To avoid user confusion, this
  # option is suppressed # from the --help menu
  parser.add_argument('--grid-count', dest='grid_count', action='store_true',
      default=False, help=argparse.SUPPRESS)

  # Adds database support using the common infrastructure
  # N.B.: Only databases with 'video' support
  import antispoofing.utils.db 
  antispoofing.utils.db.Database.create_parser(parser, 'video')

  args = parser.parse_args()

  # checks window size and overlap
  if args.window_size <= 0:
    parser.error("window-size has to be greater than 0")
  if args.overlap >= args.window_size or args.overlap < 0:
    parser.error("overlap has to be smaller than window-size and greater or equal zero")

  from .. import cluster_5quantities

  # Creates an instance of the database
  db = args.cls(args)

  real, attack = db.get_all_data()
  process = real + attack

  if args.grid_count:
    print len(process)
    sys.exit(0)
 
  # if we are on a grid environment, just find what I have to process.
  if os.environ.has_key('SGE_TASK_ID'):
    pos = int(os.environ['SGE_TASK_ID']) - 1
    if pos >= len(process):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, len(process))
    process = [process[pos]]

  sys.stdout.write('Processing %d file(s)\n' % len(process))
  sys.stdout.flush()

  counter = 0
  for obj in process:
    counter += 1

    sys.stdout.write("Processing file %s [%d/%d] " % (obj.make_path(args.inputdir, '.hdf5'), counter, len(process)))

    input = obj.load(args.inputdir, '.hdf5')    
    d_face = cluster_5quantities(input[:,0], args.window_size, args.overlap)
    d_bg   = cluster_5quantities(input[:,1], args.window_size, args.overlap)
    
    sys.stdout.write('Saving results to "%s"...\n' % args.outputdir)
    obj.save(numpy.hstack((d_face, d_bg)), args.outputdir, '.hdf5')
    sys.stdout.flush()

  sys.stdout.write('\n')
  sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
