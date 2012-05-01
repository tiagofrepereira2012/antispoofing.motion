#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Thu 28 Jul 2011 14:18:23 CEST 

"""This script can train a bob MLP machine to perform discrimination based
on input derived from one or more sets of the 5-quantities we can produce from
normalized frame differences.
"""

import os
import sys
import time
import bob
import argparse
from ... import ml

def main():
  """Main method"""

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUT_DIR = os.path.join(basedir, 'clustered')
  OUTPUT_DIR = os.path.join(basedir, 'window_based')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-d', '--output-dir', dest='outputdir', metavar='DIR', type=str, default=OUTPUT_DIR, help='Base directory that will be used to save the results. The given value will be interpolated with time.strftime and then, os.environ (in this order), so you can include %%()s strings with that to make up the final output directory (defaults to "%(default)s").')
  parser.add_argument('-v', '--input-dir', dest='inputdir', metavar='DIR', type=str, default=INPUT_DIR, help='Base directory containing the scores to be loaded. Final scores will be generated from the input directories and concatenated column-wise to form the final training matrix (defaults to "%(default)s").')
  parser.add_argument('-b', '--batch-size', metavar='INT', type=int,
      dest='batch', default=200, help='The number of samples per training iteration. Good values are greater than 100. Defaults to %(default)s')
  parser.add_argument('-e', '--epoch', metavar='INT', type=int,
      dest='epoch', default=1, help='This is the number of training steps that need to be executed before we attempt to measure the error on the development set. Defaults to %(default)s')
  parser.add_argument('-n', '--hidden-neurons', metavar='INT', type=int,
      dest='nhidden', default=5, help='The number hidden neurons in the (single) hidden layer of the MLP. Defaults to %(default)s')
  parser.add_argument('-m', '--maximum-iterations', metavar='INT', type=int,
      dest='maxiter', default=0, help='The maximum number of iterations to train for. A value of zero trains until a valley is detected on the development set. Defaults to %(default)s')
  parser.add_argument('-i', '--no-improvements', metavar='INT', type=int,
      dest='noimprov', default=0, help='The maximum number of iterations to wait for in case no improvements happen in the development set average RMSE. If that number of iterations is reached, the training is stopped. Values in the order of 10-20%% of the maximum number of iterations should be a reasonable default. If set to zero, do not consider this stop criteria. Defaults to %(default)s')
  parser.add_argument('-f', '--overwrite', action='store_true', 
      dest='overwrite', default=False, help='If set and the destination directory exists, overwrite the results contained there')
  parser.add_argument('-V', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  support_choices = ('fixed', 'hand', 'hand+fixed')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str, 
      default='hand+fixed', dest='support', help='If you would like to select a specific support to be used, use this option; if unset, use all supports', choices=support_choices)

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % k)

  if args.support == 'hand+fixed': args.support = ('hand', 'fixed')

  use_outputdir = time.strftime(args.outputdir) #interpolate time
  use_outputdir = use_outputdir % os.environ #interpolate environment
  if os.path.exists(use_outputdir):
    if not args.overwrite:
      parser.error("output directory '%s' exists and the overwrite flag was not set" % use_outputdir)
  else:
    bob.db.utils.makedirs_safe(use_outputdir)
    
  if args.verbose: print "Output directory set to \"%s\"" % use_outputdir

  # create a link to the data directory at the output directory so we keep
  # track of where the data came from.
  use_inputdir = []
  link = os.path.join(use_outputdir, "dataset")
  if os.path.lexists(link): os.unlink(link)
  if args.verbose: print "Creating link to data directory..."
  os.symlink(os.path.realpath(args.inputdir), link)
  use_inputdir.append(link)

  if args.verbose: print "Loading input files..."
  data = ml.pack.replay(use_inputdir, 'print', args.support)
  if args.verbose:
    print "Train/real  :", len(data['train']['real'])
    print "Train/attack:", len(data['train']['attack'])
    print "Devel/real  :", len(data['devel']['real'])
    print "Devel/attack:", len(data['devel']['attack'])
    print "Test /real  :", len(data['test']['real'])
    print "Test /attack:", len(data['test']['attack'])

  if args.verbose: print "Training MLP..."
  mlp, evolution = ml.rprop.make_mlp((data['train']['real'],
    data['train']['attack']), (data['devel']['real'], data['devel']['attack']),
    args.batch, args.nhidden, args.epoch, args.maxiter, args.noimprov,
    args.verbose)

  if args.verbose: print "Saving training parameters..."
  paramfile = open(os.path.join(use_outputdir, 'parameters.txt'), 'wt')
  paramfile.write('script: %s\n' % os.path.realpath(sys.argv[0]))
  paramfile.write('data  : %s\n' % [os.path.realpath(k) for k in use_inputdir])
  paramfile.write('output: %s\n' % os.path.realpath(use_outputdir))
  paramfile.write('batch size: %d\n' % args.batch)
  paramfile.write('epoch size: %d\n' % args.epoch)
  paramfile.write('hidden neurons: %d\n' % args.nhidden)
  paramfile.write('maximum iterations: %d\n' % args.maxiter)
  paramfile.write('command line: %s\n' % ' '.join(sys.argv))
  paramfile.write('protocol: %s\n' % 'print')
  write_support = args.support
  if isinstance(write_support, (tuple,list)):
    write_support = '+'.join(args.support)
  elif write_support is None: write_support = '+'.join(('hand','fixed'))
  paramfile.write('support : %s\n' % write_support)
  del paramfile
  
  if args.verbose: print "Saving MLP..."
  mlpfile = bob.io.HDF5File(os.path.join(use_outputdir, 'mlp.hdf5'),'w')
  mlp.save(mlpfile)
  del mlpfile

  if args.verbose: print "Saving result evolution..."
  evofile = bob.io.HDF5File(os.path.join(use_outputdir, 'training-evolution.hdf5'),'w')
  evolution.save(evofile)
  del evofile

  if args.verbose: print "Running analysis..."
  evolution.report(mlp, (data['test']['real'], data['test']['attack']),
      os.path.join(use_outputdir, 'plots.pdf'),
      os.path.join(use_outputdir, 'error.txt'))
  
  if args.verbose: print "All done, bye!"
 
if __name__ == '__main__':
  main()
