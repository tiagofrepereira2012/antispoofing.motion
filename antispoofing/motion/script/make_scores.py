#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Thu 28 Jul 2011 14:18:23 CEST 

"""This script will run feature vectors through a trained MLP and will produce
score files for every individual video file in the database.
"""

import os
import sys
import bob
import numpy
import argparse
from .. import ml
import ConfigParser

def main():
  """Main method"""
  
  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUTDIR = os.path.join(basedir, 'database')
  MLPDIR = os.path.join(basedir, 'mlp')
  OUTPUTDIR = os.path.join(basedir, 'scores')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the videos to be inspected by this procedure (defaults to "%(default)s")')
  parser.add_argument('mlpdir', metavar='DIR', type=str, default=MLPDIR, nargs='?', help='Base directory containing the trained MLP that will be used to produce the scores - all other parameters are read from the file "session.txt" living in that directory (defaults to "%(default)s").')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results (defaults to "%(default)s").')
  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if not os.path.exists(args.mlpdir):
    parser.error("MLP directory `%s' does not exist" % args.mlp)

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory `%s'..." % args.outputdir
    bob.db.utils.makedirs_safe(args.outputdir)

  session = ConfigParser.SafeConfigParser()
  session.readfp(open(os.path.join(args.mlpdir, 'session.txt'), 'rb'))

  from xbob.db.replay import Database
  db = Database()

  process = db.objects()

  mlp = bob.machine.MLP(bob.io.HDF5File(os.path.join(args.mlpdir,
    'mlp.hdf5')))

  counter = 0
  for obj in process:
    counter += 1

    if args.verbose:
      filename = obj.make_path(session.get('data', 'input'), extension='.hdf5')
      sys.stdout.write("Processing file %s [%d/%d] " % (filename, counter, len(process)))

    input = obj.load(session.get('data', 'input'), '.hdf5')
    valid_index = ~numpy.isnan(input.sum(axis=1))
    valid_data = input[valid_index,:]
    valid_output = mlp(valid_data)
    output = numpy.ndarray((len(input), 1), dtype='float64')
    output[valid_index] = valid_output
    output[~valid_index] = numpy.NaN

    obj.save(output, args.outputdir, '.hdf5')

    if args.verbose:
      sys.stdout.write('Saving results to "%s"...\n' % args.outputdir)
      sys.stdout.flush()

  if args.verbose: print "All done, bye!"
 
if __name__ == '__main__':
  main()
