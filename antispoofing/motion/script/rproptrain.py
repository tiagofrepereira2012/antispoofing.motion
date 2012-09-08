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
import datetime
import socket
import bob
import argparse
from ... import ml
import ConfigParser

def main():
  """Main method"""
  
  from xbob.db.replay import Database
  protocols = Database().protocols()

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUTDIR = os.path.join(basedir, 'clustered')
  OUTPUTDIR = os.path.join(basedir, 'mlp')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR, nargs='?', help='Base directory containing the scores to be loaded. Final scores will be generated from the input directories and concatenated column-wise to form the final training matrix (defaults to "%(default)s").')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results. The given value will be interpolated with time.strftime and then, os.environ (in this order), so you can include %%()s strings (e.g. %(SGE_TASK_ID)s) to make up the final output directory path (defaults to "%(default)s").')
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

  # featpack functionality
  protocols = Database().protocols()

  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      default='grandtest', choices=protocols, dest="protocol",
      help="The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(protocols)))

  supports = ('fixed', 'hand', 'hand+fixed')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str, 
      default='hand+fixed', dest='support', choices=supports, help="If you would like to select a specific support to be used, use this option (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(supports))) 

  args = parser.parse_args()

  start_time = time.time()
  paramfile = ConfigParser.SafeConfigParser()
  paramfile.add_section('time')
  paramfile.set('time', 'start', time.asctime())

  if args.verbose: print "Start time is", time.asctime()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if args.support == 'hand+fixed': args.support = ('hand', 'fixed')

  use_outputdir = time.strftime(args.outputdir) #interpolate time
  use_outputdir = use_outputdir % os.environ #interpolate environment
  if os.path.exists(use_outputdir):
    if not args.overwrite:
      parser.error("output directory '%s' exists and the overwrite flag was not set" % use_outputdir)
  else:
    bob.db.utils.makedirs_safe(use_outputdir)
    
  if args.verbose: print "Output directory set to \"%s\"" % use_outputdir

  use_inputdir = []
  abspath = os.path.abspath(args.inputdir)
  use_inputdir.append(abspath)

  if args.verbose: print "Loading input files for protocol:%s, support:%s..." \
      % (args.protocol, args.support)
  data = ml.pack.replay(use_inputdir, args.protocol, args.support)
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

  if args.verbose: print "Saving session information..."
  paramfile.add_section('data')
  datapath = [os.path.realpath(k) for k in use_inputdir]
  paramfile.set('data', 'input', '\n'.join(datapath))
  paramfile.set('data', 'train-real', str(len(data['train']['real'])))
  paramfile.set('data', 'train-attack', str(len(data['train']['attack'])))
  paramfile.set('data', 'devel-real', str(len(data['devel']['real'])))
  paramfile.set('data', 'devel-attack', str(len(data['devel']['attack'])))
  paramfile.set('data', 'test-real', str(len(data['test']['real'])))
  paramfile.set('data', 'test-attack', str(len(data['test']['attack'])))

  paramfile.add_section('mlp')
  paramfile.set('mlp', 'batch-size', str(args.batch))
  paramfile.set('mlp', 'epoch-size', str(args.epoch))
  paramfile.set('mlp', 'hidden-neurons', str(args.nhidden))
  paramfile.set('mlp', 'maximum-iterations', str(args.maxiter))
  cmdline = [os.path.realpath(sys.argv[0])] + sys.argv[1:]
  paramfile.set('mlp', 'command-line', ' '.join(cmdline))
  paramfile.set('mlp', 'protocol', args.protocol)
  write_support = args.support
  if isinstance(write_support, (tuple,list)):
    write_support = '\n'.join(args.support)
  elif write_support is None: write_support = '\n'.join(('hand','fixed'))
  paramfile.set('mlp', 'support', write_support)
  
  if args.verbose: print "Saving MLP..."
  mlpfile = bob.io.HDF5File(os.path.join(use_outputdir, 'mlp.hdf5'),'w')
  mlp.save(mlpfile)
  del mlpfile

  if args.verbose: print "Saving result evolution..."
  evofile = bob.io.HDF5File(os.path.join(use_outputdir,
    'training-evolution.hdf5'),'w')
  evolution.save(evofile)
  del evofile

  if args.verbose: print "Running analysis..."
  evolution.report(mlp, (data['test']['real'], data['test']['attack']),
      os.path.join(use_outputdir, 'plots.pdf'), paramfile)
  
  paramfile.set('time', 'end', time.asctime())
  total_time = int(time.time() - start_time)
  diff = datetime.timedelta(seconds=total_time)
  paramfile.set('time', 'duration', str(diff))
  paramfile.set('time', 'host', socket.getfqdn())

  if args.verbose: print "End time is", time.asctime()
  if args.verbose: print "Total training time:", str(diff)

  paramfile.write(open(os.path.join(use_outputdir, 'session.txt'), 'wb'))
  if args.verbose: print "All done, bye!"
 
if __name__ == '__main__':
  main()
