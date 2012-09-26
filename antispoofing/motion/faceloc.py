#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 19 Jul 2011 12:53:56 CEST 

"""Support methods and classes for reading face locations from text files."""

import bob
import numpy

def expand_detections(detections, nframes, max_age=-1):
  """Calculates a list of "nframes" with the best possible detections taking
  into consideration the ages of the last valid detectio on the detections
  list.

  Parameters:

  detections
    A dictionary containing keys that indicate the frame number of the
    detection and a value which is a BoundingBox object.

  nframes
    An integer indicating how many frames has the video that will be
    analyzed.

  max_age
    An integer indicating for a how many frames a detected face is valid if
    no detection occurs after such frame. A value of -1 == forever
  """

  retval = []
  curr = None
  age = 0
  for k in range(nframes):
    if detections and detections.has_key(k) and detections[k].is_valid():
      curr = detections[k]
      age = 0
    elif max_age < 0 or age < max_age:
      age += 1
    else: # no detections and age is larger than maximum allowed
      curr = None

    retval.append(curr)

  return retval

class BoundingBox:
  """Defines a bounding box object"""

  def __init__(self, x, y, width, height):
    """Initializes the bounding box object with the following configuration:

       x: upper left x coordinate
       y: upper left y coordinate
       width: total bounding box width in pixels
       height: total bounding box height in pixels
    """
    self.x = int(x)
    self.y = int(y)
    self.width = int(width)
    self.height = int(height)

  def area(self):
    return self.width * self.height

  def coordinates(self):
    """Returns the 4 coordinates of the bounding box: top-left, top-right,
    bottom-left, bottom-right."""
    return (
        (self.x, self.y),
        (self.x+self.width, self.y),
        (self.x, self.y+self.height),
        (self.x+self.width, self.y + self.height),
        )

  def is_valid(self):
    """Determines if a certain bounding box is valid"""
    return bool(self.x + self.width + self.y + self.height)

  def __str__(self):
    return "(%d+%d,%d+%d)" % (self.x, self.width, self.y, self.height)

  def __repr__(self):
    return "<BoundingBox: %s>" % str(self)

  def draw(self, image, thickness=2, color=(255,0,0)):
    """Draws a bounding box on a given image. If the image is colored, it is
    considered to be RGB in the Torch standard image representation, otherwise,
    we first convert the color into grayscale to then apply the bounding
    box."""

    if image.rank() == 2: #grayscale
      if isinstance(color, (tuple, list)):
        color = bob.ip.rgb_to_gray_u8(*color)

    # draws one line for each size of the bounding box
    for k in range(thickness):
      bob.ip.draw_box(image, self.x-k, self.y-k, self.width+2*k, 
          self.height+2*k)

def load(obj, database_root):
  """Loads the face file and returns a dictionary of detections
  
  Keyword parameters:

  obj
    The xbob.db.replay.File object containing the path to the database entry
    to load

  database_root
    The input directory containing the database root installation

  movie_length
    The original number of frames in the input movie file

  Returns a dictionary containing the frames in which detection occurred and
  with keys corresponding to BoundingBox objects.

  * Bounding box top-left X coordinate
  * Bounding box top-left Y coordinate
  * Bounding box width
  * Bounding box height

  The dictionary, before being returned, is passed through the method
  :py:func:`expand_detections`.
  """

  nframes = len(bob.io.VideoReader(obj.videofile(database_root)))
  retval = {}
  for entry in obj.bbx(database_root):
    retval[entry[0]] = BoundingBox(*[int(k) for k in entry[1:]])
  return expand_detections(retval, nframes)
