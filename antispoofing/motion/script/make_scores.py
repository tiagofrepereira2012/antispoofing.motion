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

  INPUTDIR = os.path.join(basedir, 'quantities')
  MACHINE = os.path.join(basedir, 'mlp/mlp.hdf5')
  OUTPUTDIR = os.path.join(basedir, 'scores')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the feature vectors to be inspected by this procedure (defaults to "%(default)s")')
  parser.add_argument('machine', metavar='FILE', type=str, default=MACHINE, nargs='?', help='Name of the machine containing the trained MLP or Linear Machine that will be used to produce the scores (defaults to "%(default)s").')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results (defaults to "%(default)s").')
  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  # Adds database support using the common infrastructure
  # N.B.: Only databases with 'video' support
  import antispoofing.utils.db 
  antispoofing.utils.db.Database.create_parser(parser, 'video')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if not os.path.exists(args.machine):
    parser.error("Machine file `%s' does not exist" % args.machine)

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory `%s'..." % args.outputdir
    bob.db.utils.makedirs_safe(args.outputdir)

  # Creates an instance of the database
  db = args.cls(args)
  real, attack = db.get_all_data()
  process = real + attack

  macfile = bob.io.HDF5File(args.machine)

  try:
    machine = bob.machine.MLP(macfile)
  except:
    try:
      machine = bob.machine.LinearMachine(macfile)
    except:
      print "Cannot load Linear or MLP machine from file %s" % args.machine
      raise

  counter = 0
  for obj in process:
    counter += 1

    if args.verbose:
      filename = obj.make_path(args.inputdir, extension='.hdf5')
      sys.stdout.write("Processing file %s [%d/%d] " % (filename, counter, len(process)))

    input = obj.load(args.inputdir, '.hdf5')
    valid_index = ~numpy.isnan(input.sum(axis=1))
    valid_data = input[valid_index,:]
    valid_output = machine(valid_data)
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
