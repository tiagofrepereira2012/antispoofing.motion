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
  
  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument('inputdir', metavar='DIR', type=str, help='Base directory containing the scores to be loaded and merged')

  parser.add_argument('outputdir', metavar='DIR', type=str, help='Base output directory for every file created by this procedure')
  
  parser.add_argument('-n', '--average', metavar='INT', type=int, default=11,
      dest='average', help="Number of scores to merge from every file (defaults to %(default)s)")

  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  # Adds database support using the common infrastructure
  # N.B.: Only databases with 'video' support
  import antispoofing.utils.db 
  antispoofing.utils.db.Database.create_parser(parser, 'video')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)

  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory %s..." % args.outputdir
    os.makedirs(args.outputdir)

  db = args.cls(args)

  def write_file(group):

    if args.verbose:
      print "Processing '%s' group..." % group
  
    out = open(os.path.join(args.outputdir, '%s-5col.txt' % group), 'wt')

    if group == 'train': reals, attacks = db.get_train_data()
    elif group == 'devel': reals, attacks = db.get_devel_data()
    elif group == 'test': reals, attacks = db.get_test_data()
    else: raise RuntimeError, "group parameter has to be train, devel or test"

    total = len(reals) + len(attacks)

    counter = 0
    for obj in reals:
      counter += 1

      if args.verbose: 
        print "Processing file %s [%d/%d]..." % (obj.make_path(), counter, total)

      arr = obj.load(args.inputdir, '.hdf5')
      arr = arr[~numpy.isnan(arr)] #remove NaN entries => invalid
      avg = numpy.mean(arr[:args.average])

      # This is a tremendous disencapsulation, but can't do it better for now
      client_id = obj._File__f.client.id
      
      out.write('%d %d %d %s %.5e\n' % (client_id, client_id, client_id,
        obj.make_path(), avg))

    for obj in attacks:
      counter += 1

      if args.verbose: 
        print "Processing file %s [%d/%d]..." % (obj.make_path(), counter, total)

      arr = obj.load(args.inputdir, '.hdf5')
      arr = arr[~numpy.isnan(arr)] #remove NaN entries => invalid
      avg = numpy.mean(arr[:args.average])
      
      # This is a tremendous disencapsulation, but can't do it better for now
      client_id = obj._File__f.client.id
      
      out.write('%d %d attack %s %.5e\n' % (client_id, client_id,
        obj.make_path(), avg))

    out.close()

  write_file('train')
  write_file('devel')
  write_file('test')
