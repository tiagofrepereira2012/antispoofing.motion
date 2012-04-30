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

INPUT_DIR = '/idiap/home/aanjos/work/spoofing/spooflib/features/framediffs/KeyLemonFaceDetector+NoNormalization/full'

def main():

  import bob
  import numpy

  protocols = bob.db.replay.Database().protocols()

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--diffs-dir', metavar='DIR', type=str,
      dest='inputdir', nargs='+', help='Base directories containing the frame differences to be treated by this procedure')
  parser.add_argument('-i', '--id', metavar='FILEID', type=int, nargs='*',
      dest="ids", help='The input file replay attack database id(s), will limit the number of files to be treated. Otherwise we treat all files.')
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      dest="protocol", help='The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on',
      choices=protocols)
  parser.add_argument('-d', '--directory', dest="directory", default='tmp', help="if given, this path will be prepended to every file output by this procedure (defaults to '%(default)s')")
  parser.add_argument('-e', '--extension', dest="extension", default='.hdf5', help="if given, this extension will be appended to every file output by this procedure (defaults to '%(default)s')")
  parser.add_argument('-n', '--window-size', dest="window_size", default=20,
      type=int, help="determines the window size to be used when clustering frame-difference observations (defaults to %(default)s)"),
  parser.add_argument('-o', '--overlap', dest="overlap", default=0, type=int,
      help="determines the window overlapping; this number has to be between 0 (no overlapping) and 'window-size'-1 (defaults to %(default)s)"),
  parser.add_argument('--grid', dest='grid', action='store_true',
      default=False, help='If set, assumes it is being run using a parametric grid job. It orders all ids to be processed and picks the one at the position given by ${SGE_TASK_ID}-1')

  args = parser.parse_args()

  # checks window size and overlap
  if args.window_size <= 0:
    parser.error("window-size has to be greater than 0")
  if args.overlap >= args.window_size or args.overlap < 0:
    parser.error("overlap has to be smaller than window-size and greater or equal zero")

  from .. import spoof

  db = bob.db.replay.Database()

  if args.protocol:
    process = [db.files(directory=k, extension='.hdf5', 
      protocol=args.protocol) for k in args.inputdir]
    
    # transform a list of dictionaries into a dictionary of lists
    process = dict(zip(process[0].keys(), zip(*[k.values() for k in process])))
  
  else:
    process = [db.files(directory=k, extension='.hdf5') for k in args.inputdir]
  
    # transform a list of dictionaries into a dictionary of lists
    process = dict(zip(process[0].keys(), zip(*[k.values() for k in process])))

    if args.ids:
      for k in process.keys():
        if k not in args.ids: del process[k]

  # finally, if we are on a grid environment, just find what I have to process.
  if args.grid:
    pos = int(os.environ['SGE_TASK_ID']) - 1
    ordered_keys = sorted(process.keys())
    if pos >= len(ordered_keys):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, len(ordered_keys))
    key = ordered_keys[pos] # gets the right key
    process = {key: process[key]}

  sys.stdout.write('Processing %d file(s)\n' % len(process))
  sys.stdout.flush()

  for key, filenames in process.items():
     
    filenames = [os.path.expanduser(k) for k in filenames]

    for k in filenames:
      sys.stdout.write('Loading %s...\n' % k)
      sys.stdout.flush()

    inputs = [bob.io.load(k) for k in filenames]

    data = [spoof.cluster_5quantities(k, args.window_size, args.overlap) for k in inputs]

    arrs = [numpy.array(k, dtype='float64') for k in data]

    # concatenate
    arr = numpy.vstack(arrs)

    sys.stdout.write('Saving results to "%s"...\n' % args.directory)
    sys.stdout.flush()
    db.save_one(key, arr, directory=args.directory, extension=args.extension)

  sys.stdout.write('\n')
  sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
