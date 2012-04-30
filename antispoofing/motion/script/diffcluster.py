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

  INPUT_DIR = os.path.join(basedir, 'framediff')
  OUTPUT_DIR = os.path.join(basedir, 'clustered')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--input-dir', metavar='DIR', type=str,
      dest='inputdir', default=INPUT_DIR, help='Base directory containing the frame differences to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('-d', '--directory', dest="directory", default=OUTPUT_DIR, help="if given, this path will be prepended to every file output by this procedure (defaults to '%(default)s')")
  parser.add_argument('-n', '--window-size', dest="window_size", default=20,
      type=int, help="determines the window size to be used when clustering frame-difference observations (defaults to %(default)s)"),
  parser.add_argument('-o', '--overlap', dest="overlap", default=0, type=int,
      help="determines the window overlapping; this number has to be between 0 (no overlapping) and 'window-size'-1 (defaults to %(default)s)"),

  args = parser.parse_args()

  # checks window size and overlap
  if args.window_size <= 0:
    parser.error("window-size has to be greater than 0")
  if args.overlap >= args.window_size or args.overlap < 0:
    parser.error("overlap has to be smaller than window-size and greater or equal zero")

  from .. import cluster_5quantities

  db = bob.db.replay.Database()

  process = db.files(directory=args.inputdir, extension='.hdf5', protocol='print')
  
  sys.stdout.write('Processing %d file(s)\n' % len(process))
  sys.stdout.flush()

  counter = 0
  for key, filename in process.items():
    counter += 1
     
    filename = os.path.expanduser(filename)
    
    sys.stdout.write("Processing file %s [%d/%d] " % (filename, counter, len(process)))

    input = bob.io.load(filename)
    
    d_face = cluster_5quantities(input[:,0], args.window_size, args.overlap)
    d_bg   = cluster_5quantities(input[:,1], args.window_size, args.overlap)
    arr = numpy.hstack((d_face, d_bg))
    db.save_one(key, arr, directory=args.directory, extension='.hdf5')
    sys.stdout.write('Saving results to "%s"...\n' % args.directory)
    sys.stdout.flush()

  sys.stdout.write('\n')
  sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
