#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 27 Feb 2012 16:01:34 CET 

"""Instructions for separating features according to protocols.
"""

import os
import sys
import bob
import numpy
import argparse

def replay(inputs, protocol, support, groups=('train', 'devel', 'test'),
    cls=('attack','real'), device='any'):
  """Combines (possibly several) inputs to form train, development and test
  arraysets for the replay attack database.

  Parameters
    inputs
      Base directories containing the scores to be loaded and merged. The
      directories given as parameters here should contain the "rcd" and "rad"
      directories of the replay attack database.

    protocol
      One of the valid protocols in the replay attack database.

    support
      Either 'hand' or 'fixed'. If ``None`` is given, use data with both
      supports.

    groups
      A single group to pack data for or all groups in "train", "devel" or
      "test" - as a tuple

    cls
      A single class to pack data for or all classes in "attack", "real" - as a
      tuple

    device
      Allows you to filter the results by device: 'any' or 'all', or None just
      make me ignore that parameter. Other valid values are 'print', 'mobile' 
      or 'highdef'

  Returns
    Six bob.io.Arraysets that contain real-accesses and attacks for training,
    development and testing, organized as a dictionary like this::

      {
        'train': {
          'real': bob.io.Arrayset,
          'attack': bob.io.Arrayset,
          },
        'devel': {
          'real': bob.io.Arrayset,
          'attack': bob.io.Arrayset,
          },
        'test': {
          'real': bob.io.Arrayset,
          'attack': bob.io.Arrayset,
          },
      }
  """

  def make_arrayset(basedirs, stems, ext):
    """Loads the data from <basedir>/<stem><ext> and produces merged
    data sets of feature vectors.
    """
    retval = []
    for S in stems: 
      retval.append(numpy.hstack([bob.io.load(os.path.join(k, S) + ext) for k in basedirs]))
    return numpy.vstack(retval)

  def group_files(db, inputs, protocol, support, group, cls, device):
    """DRY grouping method"""

    files = db.files(support=support, protocol=protocol, groups=(group,),
        cls=cls).values()
    
    if device not in ('any', 'all', None):
      search_str = 'attack_%s' % device
      files = [k for k in files if k.find(search_str) >= 0]

    return make_arrayset(inputs, files, '.hdf5')
  
  if isinstance(groups, (str,unicode)): groups = (groups,)
  if isinstance(cls, (str,unicode)): cls = (cls,)

  db = bob.db.replay.Database()

  retval = {}

  for gr in groups:
    for cl in cls:
      gdict = retval.setdefault(gr,{})
      gdict[cl] = group_files(db, inputs, protocol, support, gr, cl, device)

  return retval
