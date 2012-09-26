#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Sun 09 Sep 2012 12:42:38 CEST 

"""Merge multiple scores in score files and produce 5-column text files for the
whole database. Every line in the 5-column output file represents 1 video in
the database. Scores for every video are averaged according to options given to
this script before set in the output file.
"""

import os
import sys
import bob
import numpy
import argparse

def main():
  """Main method"""
  
  from xbob.db.replay import Database

  protocols = [k.name for k in Database().protocols()]

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, help='Base directory containing the scores to be loaded and merged')
  parser.add_argument('outputdir', metavar='DIR', type=str, help='Base output directory for every file created by this procedure')
  
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      default='grandtest', choices=protocols, dest="protocol",
      help="The protocol type may be specified to subselect a smaller number of files to operate on (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(protocols)))

  supports = ('fixed', 'hand', 'hand+fixed')

  parser.add_argument('-s', '--support', metavar='SUPPORT', type=str, 
      default='hand+fixed', dest='support', choices=supports, help="If you would like to select a specific support to be used, use this option (one of '%s'; defaults to '%%(default)s')" % '|'.join(sorted(supports))) 

  parser.add_argument('-n', '--average', metavar='INT', type=int, default=11,
      dest='average', help="Number of scores to merge from every file (defaults to %(default)s)")

  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if args.support == 'hand+fixed': args.support = ('hand', 'fixed')

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory %s..." % args.outputdir
    os.makedirs(args.outputdir)

  db = Database()

  def write_file(group):

    if args.verbose:
      print "Processing '%s' group..." % group
  
    out = open(os.path.join(args.outputdir, '%s-5col.txt' % group), 'wt')

    reals = db.objects(protocol=args.protocol, support=args.support,
        groups=(group,), cls=('real',))
    attacks = db.objects(protocol=args.protocol, support=args.support,
        groups=(group,), cls=('attack',))
    total = len(reals) + len(attacks)

    counter = 0
    for obj in reals:
      counter += 1

      if args.verbose: 
        print "Processing file %s [%d/%d]..." % (obj.path, counter, total)

      arr = obj.load(args.inputdir, '.hdf5')
      arr = arr[~numpy.isnan(arr)] #remove NaN entries => invalid
      avg = numpy.mean(arr[:args.average])
      
      out.write('%d %d %d %s %.5e\n' % (obj.client.id, obj.client.id,
        obj.client.id, obj.path, avg))

    for obj in attacks:
      counter += 1

      if args.verbose: 
        print "Processing file %s [%d/%d]..." % (obj.path, counter, total)

      arr = obj.load(args.inputdir, '.hdf5')
      arr = arr[~numpy.isnan(arr)] #remove NaN entries => invalid
      avg = numpy.mean(arr[:args.average])
      
      out.write('%d %d attack %s %.5e\n' % (obj.client.id, obj.client.id,
        obj.path, avg))

    out.close()

  write_file('train')
  write_file('devel')
  write_file('test')
