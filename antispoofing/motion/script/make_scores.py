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
import argparse
from .. import ml
import ConfigParser

def main():
  """Main method"""
  
  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUTDIR = os.path.join(basedir, 'mlp')
  OUTPUTDIR = os.path.join(basedir, 'scores')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR, nargs='?', help='Base directory containing the trained MLP that will be used to produce the scores - all other parameters are read from the file "session.txt" living in that directory (defaults to "%(default)s").')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results (defaults to "%(default)s").')
  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory `%s'..." % args.outputdir
    bob.db.utils.makedirs_safe(args.outputdir)

  session = ConfigParser.SafeConfigParser()
  session.readfp(open(os.path.join(args.inputdir, 'session.txt'), 'rb'))
    
  from xbob.db.replay import Database
  db = Database()

  process = db.files(directory=session.get('data', 'input'), extension='.hdf5', 
      protocol=session.get('mlp', 'protocol'), 
      support=session.get('mlp', 'support').split())

  mlp = bob.machine.MLP(bob.io.HDF5File(os.path.join(args.inputdir,
    'mlp.hdf5')))

  counter = 0
  for key, filename in process.items():
    counter += 1
     
    filename = os.path.expanduser(filename)
    
    if args.verbose: sys.stdout.write("Processing file %s [%d/%d] " % (filename, counter, len(process)))

    input = bob.io.load(filename)

    output = mlp(input)

    db.save_one(key, output, directory=args.outputdir, extension='.hdf5')

    if args.verbose:
      sys.stdout.write('Saving results to "%s"...\n' % args.outputdir)
      sys.stdout.flush()

  if args.verbose: print "All done, bye!"
 
if __name__ == '__main__':
  main()
