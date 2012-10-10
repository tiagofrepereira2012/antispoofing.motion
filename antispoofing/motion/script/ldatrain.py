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
import numpy
import argparse
from .. import ml
import ConfigParser

def main():
  """Main method"""
  
  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUTDIR = os.path.join(basedir, 'quantities')
  OUTPUTDIR = os.path.join(basedir, 'lda')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR, nargs='?', help='Base directory containing the 5-quantities to be loaded. Final MLP input will be generated from the input directory and concatenated column-wise to form the final training matrix (defaults to "%(default)s").')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR, nargs='?', help='Base directory that will be used to save the results. The given value will be interpolated with time.strftime and then, os.environ (in this order), so you can include %%()s strings (e.g. %%(SGE_TASK_ID)s) to make up the final output directory path (defaults to "%(default)s").')
  parser.add_argument('-f', '--overwrite', action='store_true', 
      dest='overwrite', default=False, help='If set and the destination directory exists, overwrite the results contained there')
  parser.add_argument('-V', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  # Adds database support using the common infrastructure
  # N.B.: Only databases with 'video' support
  import antispoofing.utils.db 
  antispoofing.utils.db.Database.create_parser(parser, 'video')

  args = parser.parse_args()

  start_time = time.time()
  paramfile = ConfigParser.SafeConfigParser()
  paramfile.add_section('time')
  paramfile.set('time', 'start', time.asctime())

  if args.verbose: print "Start time is", time.asctime()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

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

  if args.verbose: print "Loading non-NaN entries from input files at '%s' database..." % args.name
  db = args.cls(args) 
  real, attack = db.get_train_data()
  
  def merge_data(flist):
    d = bob.io.load([k.make_path(use_inputdir[0], '.hdf5') for k in flist])
    return d[~numpy.isnan(d.sum(axis=1)),:]

  real = merge_data(real)
  attack = merge_data(attack)

  if args.verbose: print "Evaluating mean and standard deviation..."
  from antispoofing.utils.ml.norm import calc_mean_std
  mean, std = calc_mean_std(real, attack, nonStdZero=True)

  if args.verbose: print "Training LDA..."
  from antispoofing.utils.ml.norm import zeromean_unitvar_norm
  real = zeromean_unitvar_norm(real, mean, std)
  attack = zeromean_unitvar_norm(attack, mean, std)
  from antispoofing.utils.ml.lda import make_lda
  machine = make_lda([real, attack])

  # adjust some details of the final machine to be saved
  machine.resize(machine.shape[0], 1)
  
  # so we get real and attacks on the "right" side of the axis
  machine.weights = -1 * machine.weights

  machine.input_subtract = mean
  machine.input_divide = std

  if args.verbose: print "Performance evaluation:"
  real, attack = db.get_devel_data()
  real = merge_data(real)
  attack = merge_data(attack)
  pos = machine(real)[:,0]
  neg = machine(attack)[:,0]

  thres = bob.measure.eer_threshold(neg, pos)
  
  far, frr = bob.measure.farfrr(neg, pos, thres)
  good_neg = bob.measure.correctly_classified_negatives(neg, thres).sum()
  good_pos = bob.measure.correctly_classified_positives(pos, thres).sum()
  print " -> EER @ devel set threshold: %.5e" % thres
  print " -> Devel set results:"
  print "     * FAR : %.3f%% (%d/%d)" % (100*far, len(neg)-good_neg, len(neg))
  print "     * FRR : %.3f%% (%d/%d)" % (100*frr, len(pos)-good_pos, len(pos))
  print "     * HTER: %.3f%%" % (50*(far+frr))
  
  real, attack = db.get_test_data()
  real = merge_data(real)
  attack = merge_data(attack)
  pos = machine(real)[:,0]
  neg = machine(attack)[:,0]
  far, frr = bob.measure.farfrr(neg, pos, thres)
  good_neg = bob.measure.correctly_classified_negatives(neg, thres).sum()
  good_pos = bob.measure.correctly_classified_positives(pos, thres).sum()
  print " -> Test set results:"
  print "     * FAR: %.3f%% (%d/%d)" % (100*far, len(neg)-good_neg, len(neg))
  print "     * FRR: %.3f%% (%d/%d)" % (100*frr, len(pos)-good_pos, len(pos))
  print "     * HTER: %.3f%%" % (50*(far+frr))

  if args.verbose: print "Saving session information..."
  def get_version(package):
    __import__('pkg_resources').require(package)[0].version

  paramfile.add_section('software')
  for package in __import__('pkg_resources').require('antispoofing.motion'):
    paramfile.set('software', package.key, package.version)

  paramfile.add_section('environment')
  cmdline = [os.path.realpath(sys.argv[0])] + sys.argv[1:]
  paramfile.set('environment', 'command-line', ' '.join(cmdline))

  paramfile.add_section('data')
  datapath = [os.path.realpath(k) for k in use_inputdir]
  paramfile.set('data', 'database', args.name)
  paramfile.set('data', 'input', '\n'.join(datapath))
  paramfile.set('data', 'train-real', str(len(real)))
  paramfile.set('data', 'train-attack', str(len(attack)))

  paramfile.add_section('lda')
  paramfile.set('lda', 'shape', '-'.join([str(k) for k in machine.shape]))
  
  if args.verbose: print "Saving LDA machine..."
  machfile = bob.io.HDF5File(os.path.join(use_outputdir, 'lda.hdf5'),'w')
  machine.save(machfile)
  del machfile

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
