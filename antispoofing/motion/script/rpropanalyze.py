#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Thu 28 Jul 2011 14:18:23 CEST 

"""This script can run a bob MLP machine that performs discrimination based
on input derived from one or more sets of the 5-quantities we can produce from
normalized frame differences.
"""

import os
import sys
import time
import bob
import numpy
import argparse
from .. import ml
import fnmatch

def main():
  """Main method"""

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str,
      help='Base directory containing the machine to be loaded')
  
  # featpack functionality
  protocol_choices = bob.db.replay.Database().protocols()

  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      dest='protocol', default='grandtest', help='Specific protocol to use for training and testing the detector (defaults to "%(default)s)")', 
      choices=protocol_choices)

  support_choices = ('fixed', 'hand', 'hand+fixed')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str, 
      default='hand+fixed', dest='support', help='If you would like to select a specific support to be used, use this option; if unset, use all supports', choices=support_choices)

  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  args = parser.parse_args()
  if not os.path.exists(args.inputdir):
    parser.error("input directory does not exist")

  if args.support == 'hand+fixed': args.support = ('hand', 'fixed')

  if args.verbose: print "Re-running analysis on \"%s\"..." % args.inputdir

  if args.verbose: print "Loading input files..."

  #input data directories
  datadir = [os.path.join(args.inputdir, k) for k in sorted(fnmatch.filter(os.listdir(args.inputdir), 'dataset*'))]

  #reload data
  data = ml.pack.replay(datadir, args.protocol, args.support)

  if args.verbose:
    print "Train/real  :", len(data['train']['real'])
    print "Train/attack:", len(data['train']['attack'])
    print "Devel/real  :", len(data['devel']['real'])
    print "Devel/attack:", len(data['devel']['attack'])
    print "Test /real  :", len(data['test']['real'])
    print "Test /attack:", len(data['test']['attack'])

  if args.verbose: print "Running MLP analysis..."
  
  target = [
      numpy.array([+1], 'float64'),
      numpy.array([-1], 'float64'),
      ]

  analyzer = ml.rprop.Analyzer((data['train']['real'], data['train']['attack']),
      (data['devel']['real'], data['devel']['attack']), target)

  evo_data = bob.io.HDF5File(os.path.join(args.inputdir,
    'training-evolution.hdf5'), 'r') #read-only
  analyzer.load(evo_data)
 
  mlp_data = bob.io.HDF5File(os.path.join(args.inputdir, 'mlp.hdf5'), 'r')
  mlp = bob.machine.MLP(mlp_data)

  analyzer.report(mlp, (data['test']['real'], data['test']['attack']),
      os.path.join(args.inputdir, 'plots.pdf'),
      os.path.join(args.inputdir, 'error.txt'))
  
  if args.verbose: print "All done, bye!"
 
if __name__ == '__main__':
  main()
