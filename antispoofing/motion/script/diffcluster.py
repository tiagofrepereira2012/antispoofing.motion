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
  from xbob.db.replay import Database

  protocols = [k.name() for k in Database().protocols()]

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'framediff')
  OUTPUTDIR = os.path.join(basedir, 'clustered')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the frame differences to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR,
      nargs='?', help='Base output directory for every file created by this procedure (defaults to "%(default)s")')
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      default='grandtest', choices=protocols, dest="protocol",
      help="The protocol type may be specified to subselect a smaller number of files to operate on (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(protocols)))

  supports = ('fixed', 'hand', 'hand+fixed')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str,
      default='hand+fixed', dest='support', choices=supports, help="If you would like to select a specific support to be used, use this option (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(supports)))

  parser.add_argument('-n', '--window-size', dest="window_size", default=20,
      type=int, help="determines the window size to be used when clustering frame-difference observations (defaults to %(default)s)"),
  parser.add_argument('-o', '--overlap', dest="overlap", default=0, type=int,
      help="determines the window overlapping; this number has to be between 0 (no overlapping) and 'window-size'-1 (defaults to %(default)s)"),

  # The next option just returns the total number of cases we will be running
  # It can be used to set jman --array option. To avoid user confusion, this
  # option is suppressed # from the --help menu
  parser.add_argument('--grid-count', dest='grid_count', action='store_true',
      default=False, help=argparse.SUPPRESS)

  args = parser.parse_args()

  # checks window size and overlap
  if args.window_size <= 0:
    parser.error("window-size has to be greater than 0")
  if args.overlap >= args.window_size or args.overlap < 0:
    parser.error("overlap has to be smaller than window-size and greater or equal zero")

  if args.support == 'hand+fixed': args.support = ('hand', 'fixed')

  from .. import cluster_5quantities

  db = Database()

  process = db.objects(protocol=args.protocol, support=args.support)
  
  if args.grid_count:
    print len(process)
    sys.exit(0)
 
  # if we are on a grid environment, just find what I have to process.
  if os.environ.has_key('SGE_TASK_ID'):
    pos = int(os.environ['SGE_TASK_ID']) - 1
    ordered_keys = sorted(process.keys())
    if pos >= len(ordered_keys):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, len(ordered_keys))
    key = ordered_keys[pos] # gets the right key
    process = {key: process[key]}

  sys.stdout.write('Processing %d file(s)\n' % len(process))
  sys.stdout.flush()

  counter = 0
  for obj in process.items():
    counter += 1
     
    filename = obj.make_path(args.inputdir, '.hdf5')
 
    sys.stdout.write("Processing file %s [%d/%d] " % (filename, counter, len(process)))

    input = bob.io.load(filename)
    
    d_face = cluster_5quantities(input[:,0], args.window_size, args.overlap)
    d_bg   = cluster_5quantities(input[:,1], args.window_size, args.overlap)
    arr = numpy.hstack((d_face, d_bg))
    obj.save(arr, directory=args.outputdir, extension='.hdf5')
    sys.stdout.write('Saving results to "%s"...\n' % args.outputdir)
    sys.stdout.flush()

  sys.stdout.write('\n')
  sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
