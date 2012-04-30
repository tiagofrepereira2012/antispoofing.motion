#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 02 Aug 2010 11:31:31 CEST 

"""Calculates the normalized frame differences for all or some videos of the
replay attack database. This technique is described on the paper:
Counter-Measures to Photo Attacks in Face Recognition: a public database and a
baseline, Anjos & Marcel, IJCB'11.

This script will output a number of motion features covering one of the
following areas:

1. Full image
2. Face
3. Background
4. Eyes
5. Face Reminder
"""

import os, sys
import argparse

INPUT_DIR = '/idiap/group/replay/database/protocols'

def main():
  
  import bob
  import numpy

  protocols = bob.db.replay.Database().protocols()

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--input-dir', metavar='DIR', type=str,
      dest='inputdir', default=INPUT_DIR, help='Base directory containing the videos to be treated by this procedure (defaults to "%(default)s")')
  parser.add_argument('-i', '--id', metavar='FILEID', type=int, nargs='*',
      dest="ids", help='The input file replay attack database id(s), will limit the number of files to be treated. Otherwise we treat all files.')
  parser.add_argument('-p', '--protocol', metavar='PROTOCOL', type=str,
      dest="protocol", help='The protocol type may be specified instead of the the id switch to subselect a smaller number of files to operate on',
      choices=protocols)
  parser.add_argument('-d', '--directory', dest="directory", default='tmp', help="if given, this path will be prepended to every file output by this procedure (defaults to '%(default)s')")
  parser.add_argument('-e', '--extension', dest="extension", default='.hdf5', help="if given, this extension will be appended to every file output by this procedure (defaults to '%(default)s')")
  parser.add_argument('-f', '--face-location', metavar='DIR', type=str,
      dest="faceloc", help='If given, should be name of a directory containing the face location for the frames in the associated videos, organized in the same way as in the replay attack database.')
  parser.add_argument('-b', '--border-size', metavar='INT>=0', type=int, dest='border', default=None, help='Number of extra pixels to define the region of interest from the bounding box (defaults to \'%(default)s\').')
  parser.add_argument('-r', '--roi', metavar='ROI', type=str,
      choices=('full', 'face', 'background', 'eyes', 'face_reminder'),
      default='full', dest='roi', help='Choose the specific RoI to be processed (defaults to "%(default)s")')
  parser.add_argument('--grid', dest='grid', action='store_true',
      default=False, help='If set, assumes it is being run using a parametric grid job. It orders all ids to be processed and picks the one at the position given by ${SGE_TASK_ID}-1')

  args = parser.parse_args()

  if args.roi != 'full' and not args.faceloc:
    parser.error('To select RoI %s you need to pass the face locations directory' % args.roi)

  from .. import spoof, faceloc

  db = bob.db.replay.Database()

  if args.protocol:
    process = db.files(directory=args.inputdir, extension='.mov',
      protocol=args.protocol)
  else:
    process = db.files(directory=args.inputdir, extension='.mov')
    if args.ids:
      for k in process.keys():
        if k not in args.ids: del process[k]

  # finally, if we are on a grid environment, just find what I have to process.
  if args.grid:
    pos = int(os.environ['SGE_TASK_ID']) - 1
    ordered_keys = sorted(process.keys())
    if pos >= len(ordered_keys):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, len(ordered_keys))
    key = ordered_keys[pos] # gets the right key
    process = {key: process[key]}

  
  counter = 0
  for key, filename in process.items():
    counter += 1
    
    filename = os.path.expanduser(filename)

    input = bob.io.VideoReader(filename)

    # loads the face locations if user has specified
    if args.faceloc:
      flocfile = os.path.expanduser(db.paths([key], args.faceloc, '.face')[0])
      locations = faceloc.read_face(flocfile)
      locations = faceloc.expand_detections(locations, input.numberOfFrames)
    else:
      locations = input.numberOfFrames * [None]

    sys.stdout.write("Processing file %s (%d frames) [%d/%d] " % (filename,
      input.numberOfFrames, counter, len(process)))

    # start the work here...
    vin = input.load() # load all in one shot.
    prev = bob.ip.rgb_to_gray(vin[0,:,:,:])
    curr = numpy.empty_like(prev)
    data = [0.] #accounts for the first frame (no diff. yet)

    for k in range(1, vin.shape[0]):
      sys.stdout.write('.')
      sys.stdout.flush()
      bob.ip.rgb_to_gray(vin[k,:,:,:], curr)

      if args.roi == 'full':
        data.append(spoof.eval_fullframe_differences(prev, curr))
      elif args.roi == 'face':
        data.append(spoof.eval_face_differences(prev, curr, locations[k]))
      elif args.roi == 'background':
        data.append(spoof.eval_background_differences(prev, curr, locations[k],
          args.border))
      elif args.roi == 'eyes':
        data.append(spoof.eval_eyes_differences(prev, curr, locations[k]))
      elif args.roi == 'face_reminder':
        data.append(spoof.eval_face_reminder_differences(prev, curr, locations[k]))

      # swap buffers: curr <=> prev
      tmp = prev
      prev = curr
      curr = tmp

    sys.stdout.write('\n')
    sys.stdout.flush()

    # saves the output

    arr = numpy.array(data, dtype='float64')
    db.save_one(key, arr, directory=args.directory, extension=args.extension)

  return 0

if __name__ == "__main__":
  main()
