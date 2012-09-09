#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 02 Aug 2010 11:31:31 CEST 

"""Calculates the normalized frame differences for face and background, for all
videos of the REPLAY-ATTACK database. This technique is described on the paper:
Counter-Measures to Photo Attacks in Face Recognition: a public database and a
baseline, Anjos & Marcel, IJCB'11.  
"""

import os, sys
import argparse

def main():
  
  import bob
  import numpy
  from xbob.db.replay import Database

  protocols = Database().protocols()

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'database')
  OUTPUTDIR = os.path.join(basedir, 'framediff')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the videos to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR,
      nargs='?', help='Base output directory for every file created by this procedure defaults to "%(default)s")')
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      default='grandtest', choices=protocols, dest="protocol",
      help='The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on (one of "%s"; defaults to "%%(default)s")' % '|'.join(sorted(protocols)))
      
  # If set, assumes it is being run using a parametric grid job. It orders all
  # ids to be processed and picks the one at the position given by
  # ${SGE_TASK_ID}-1'). To avoid user confusion, this option is suppressed
  # from the --help menu
  parser.add_argument('--grid', dest='grid', action='store_true',
      default=False, help=argparse.SUPPRESS)
  # The next option just returns the total number of cases we will be running
  # It can be used to set jman --array option.
  parser.add_argument('--grid-count', dest='grid_count', action='store_true',
      default=False, help=argparse.SUPPRESS)

  args = parser.parse_args()

  from ...faceloc import read_face, expand_detections
  from .. import eval_face_differences, eval_background_differences

  db = Database()

  process = db.files(directory=args.inputdir, extension='.mov', 
      protocol=args.protocol)

  if args.grid_count:
    print len(process)
    sys.exit(0)
 
  # if we are on a grid environment, just find what I have to process.
  if args.grid:
    pos = int(os.environ['SGE_TASK_ID']) - 1
    ordered_keys = sorted(process.keys())
    if pos >= len(ordered_keys):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, len(ordered_keys))
    key = ordered_keys[pos] # gets the right key
    process = {key: process[key]}

  # where to find the face bounding boxes
  faceloc_dir = os.path.join(args.inputdir, 'face-locations')

  counter = 0
  for key, filename in process.items():
    counter += 1
 
    filename = os.path.expanduser(filename)

    input = bob.io.VideoReader(filename)

    # loads the face locations
    flocfile = os.path.expanduser(db.paths([key], faceloc_dir, '.face')[0])
    locations = read_face(flocfile)
    locations = expand_detections(locations, input.number_of_frames)

    sys.stdout.write("Processing file %s (%d frames) [%d/%d]..." % (filename,
      input.number_of_frames, counter, len(process)))

    # start the work here...
    vin = input.load() # load all in one shot.
    prev = bob.ip.rgb_to_gray(vin[0,:,:,:])
    curr = numpy.empty_like(prev)
    data = [(0.,0.)] #accounts for the first frame (no diff. yet)

    for k in range(1, vin.shape[0]):
      sys.stdout.write('.')
      sys.stdout.flush()
      bob.ip.rgb_to_gray(vin[k,:,:,:], curr)

      data.append(
          (eval_face_differences(prev, curr, locations[k]),
            eval_background_differences(prev, curr, locations[k], None)
            )
          )

      # swap buffers: curr <=> prev
      tmp = prev
      prev = curr
      curr = tmp

    # saves the output
    arr = numpy.array(data, dtype='float64')
    db.save_one(key, arr, directory=args.outputdir, extension='.hdf5')
    
    sys.stdout.write('\n')
    sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
