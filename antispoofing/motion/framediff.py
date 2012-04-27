#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 19 Jul 18:52:33 2011 

"""Support methods to compute frame differences in two image sequences.
"""

def eval_differences(previous, current, facebbx):
  """Evaluates the normalized frame difference on 5 regions:

  1. Full image
  2. Face
  3. Background
  4. Eyes
  5. Face Reminder

  If bounding_box is None or invalid, just evalute the full image frame
  difference.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A BoundingBox object containing the coordinates of the face location.

  .. note::

    This is a more processor friendly way to create these 5 features. It stands
    here as a baseline implementation. For grid analysis, the split methods 
    bellow will be more convinient as they allow for a better organization of
    data.
  """

  full_diff = abs(current.astype('int32') - previous.astype('int32'))
 
  full = full_diff.sum()

  face = bg = eyes = reminder = 0.

  if facebbx and facebbx.is_valid():

    face_diff = full_diff[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]
    
    # calculates the differences in the face and background areas
    face = face_diff.sum()
    bg = full - face

    # calculates the differences in the eyes and face reminder
    from ..faceloc import Anthropometry19x19
    eyesbbx = Anthropometry19x19(facebbx).eye_area()
    eyes_diff = full_diff[eyesbbx.y:(eyesbbx.y+eyesbbx.height),
        eyesbbx.x:(eyesbbx.x+eyesbbx.width)]

    eyes = eyes_diff.sum()
    reminder = face - eyes
    
    # normalization by area
    face /= float(face_diff.size)
    bg /= float(full_diff.size - face_diff.size)
    eyes /= float(eyes_diff.size)
    reminder /= float((face_diff.size - eyes_diff.size))

  full /= float(full_diff.size)

  return (full, face, bg, eyes, reminder)

def eval_fullframe_differences(previous, current):
  """Evaluates the normalized frame difference on the full image.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image
  """

  full_diff = abs(current.astype('int32') - previous.astype('int32'))
 
  full = full_diff.sum()

  full /= float(full_diff.size)

  return full

def eval_face_differences(previous, current, facebbx):
  """Evaluates the normalized frame difference on the face region.

  If bounding_box is None or invalid, returns 0.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A BoundingBox object containing the coordinates of the face location.
  """

  if facebbx and facebbx.is_valid():

    prev = previous[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]
    curr = current[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]

    face_diff = abs(curr.astype('int32') - prev.astype('int32'))
 
    face = face_diff.sum()

    face /= float(face_diff.size)

    return face

  return 0.

def eval_background_differences(previous, current, facebbx, border):
  """Evaluates the normalized frame difference on the background.

  If bounding_box is None or invalid, returns 0.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A BoundingBox object containing the coordinates of the face location.

  border
    The border size to consider. If set to None, consider all image from the
    face location up to the end.
  """

  full_diff = abs(current.astype('int32') - previous.astype('int32'))
 
  if border is None:
    full = full_diff.sum()
    full_size = full_diff.size

  elif facebbx and facebbx.is_valid():

    y1 = facebbx.y - border
    if y1 < 0: y1 = 0
    x1 = facebbx.x - border
    if x1 < 0: x1 = 0
    y2 = y1 + facebbx.height + (2*border)
    if y2 > full_diff.shape[0]: y2 = full_diff.shape[0]
    x2 = x1 + facebbx.width + (2*border)
    if x2 > full_diff.shape[1]: x2 = full_diff.shape[1]
    full = full_diff[y1:y2, x1:x2].sum()
    full_size = full_diff[y1:y2, x1:x2].size

  bg = 0.

  if facebbx and facebbx.is_valid():

    face_diff = full_diff[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]
    
    # calculates the differences in the face and background areas
    face = face_diff.sum()
    bg = full - face

    normalization = float(full_size - face_diff.size)
    if normalization < 1: #prevents zero division
      bg = 0.0
    else:
      bg /= float(full_size - face_diff.size)

  return bg

def eval_eyes_differences(previous, current, facebbx):
  """Evaluates the normalized frame difference on 5 regions:

  If bounding_box is None or invalid, return 0

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A BoundingBox object containing the coordinates of the face location.
  """

  eyes = 0.

  if facebbx and facebbx.is_valid():

    from ..faceloc import Anthropometry19x19
    eyesbbx = Anthropometry19x19(facebbx).eye_area()

    prev = previous[eyesbbx.y:(eyesbbx.y+eyesbbx.height),
        eyesbbx.x:(eyesbbx.x+eyesbbx.width)]
    curr = current[eyesbbx.y:(eyesbbx.y+eyesbbx.height),
        eyesbbx.x:(eyesbbx.x+eyesbbx.width)]

    eyes_diff = abs(curr.astype('int32') - prev.astype('int32'))
 
    eyes = eyes_diff.sum()

    eyes /= float(eyes_diff.size)

  return eyes

def eval_face_reminder_differences(previous, current, facebbx):
  """Evaluates the normalized frame difference on the face reminder.

  If bounding_box is None or invalid, returns 0.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A BoundingBox object containing the coordinates of the face location.
  """

  reminder = 0.

  if facebbx and facebbx.is_valid():

    prev = previous[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]
    curr = current[facebbx.y:(facebbx.y+facebbx.height),
        facebbx.x:(facebbx.x+facebbx.width)]

    face_diff = abs(curr.astype('int32') - prev.astype('int32'))
 
    face = face_diff.sum()

    # calculates the differences in the eyes and face reminder
    from ..faceloc import Anthropometry19x19
    eyesbbx = Anthropometry19x19(facebbx).eye_area()

    prev = previous[eyesbbx.y:(eyesbbx.y+eyesbbx.height),
        eyesbbx.x:(eyesbbx.x+eyesbbx.width)]
    curr = current[eyesbbx.y:(eyesbbx.y+eyesbbx.height),
        eyesbbx.x:(eyesbbx.x+eyesbbx.width)]

    eyes_diff = abs(curr.astype('int32') - prev.astype('int32'))
 
    eyes = eyes_diff.sum()

    reminder = face - eyes
    
    reminder /= float((face_diff.size - eyes_diff.size))

  return reminder
