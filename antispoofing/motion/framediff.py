#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 19 Jul 18:52:33 2011 

"""Support methods to compute frame differences in two image sequences.
"""

def eval_face_differences(previous, current, facebbx):
  """Evaluates the normalized frame difference on the face region.

  If bounding_box is None or invalid, returns 0.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A valid BoundingBox object containing the coordinates of the face location.
  """

  prev = previous[facebbx.y:(facebbx.y+facebbx.height),
      facebbx.x:(facebbx.x+facebbx.width)]
  curr = current[facebbx.y:(facebbx.y+facebbx.height),
      facebbx.x:(facebbx.x+facebbx.width)]

  face_diff = abs(curr.astype('int32') - prev.astype('int32'))

  face = face_diff.sum()

  face /= float(face_diff.size)

  return face

def eval_background_differences(previous, current, facebbx, border):
  """Evaluates the normalized frame difference on the background.

  If bounding_box is None or invalid, returns 0.

  Keyword Parameters:

  previous
    Previous frame as a gray-scaled image

  current
    The current frame as a gray-scaled image

  facebbx
    A valid BoundingBox object containing the coordinates of the face location.

  border
    The border size to consider. If set to None, consider all image from the
    face location up to the end.
  """

  full_diff = abs(current.astype('int32') - previous.astype('int32'))
 
  if border is None:
    full = full_diff.sum()
    full_size = full_diff.size

  else:

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
