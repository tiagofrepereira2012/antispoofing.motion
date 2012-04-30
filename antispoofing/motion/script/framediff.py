#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 02 Aug 2010 11:31:31 CEST 

"""Calculates the normalized frame differences for all videos of the
PRINT-ATTACK database. This technique is described on the paper:
Counter-Measures to Photo Attacks in Face Recognition: a public database and a
baseline, Anjos & Marcel, IJCB'11.
"""

import os, sys
import argparse

def main():
  
  import bob
  import numpy

  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

  INPUT_DIR = os.path.join(basedir, 'database')
  OUTPUT_DIR = os.path.join(basedir, 'framediff')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--input-dir', metavar='DIR', type=str,
      dest='inputdir', default=INPUT_DIR, help='Base directory containing the videos to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('-d', '--directory', dest="directory", default=OUTPUT_DIR, help="if given, this path will be prepended to every file output by this procedure (defaults to '%(default)s')")

  args = parser.parse_args()

  from ...faceloc import read_face, expand_detections
  from .. import eval_face_differences, eval_background_differences

  db = bob.db.replay.Database()

  process = db.files(directory=args.inputdir, extension='.mov', 
      protocol='print')
  
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
    db.save_one(key, arr, directory=args.directory, extension='.hdf5')
    
    sys.stdout.write('\n')
    sys.stdout.flush()

  return 0

if __name__ == "__main__":
  main()
