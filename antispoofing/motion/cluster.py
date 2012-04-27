#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 26 Jul 2011 12:27:28 CEST 

"""Algorithms for clustering frame-diff data.
"""
import sys

def dcratio(arr):
  """Calculates the DC ratio as defined by the following formula
  
  .. math::

    D(N) = \frac{\sum_{i=1}^N{|FFT_i|}}{|FFT_0|}
  """

  if arr.shape[0] <= 1: return 0.

  import bob
  import numpy

  res = bob.sp.fft(arr.astype('complex128'))
  res = numpy.absolute(res) #absolute value

  if res[0] == 0:
    s = sum(res[1:])
    if s > 0: return sys.float_info.max
    elif s < 0: return -sys.float_info.max
    else: return 0

  return sum(res[1:])/res[0]

def cluster_5quantities(arr, window_size, overlap):
  """Calculates the clustered values as described at the paper:
  Counter-Measures to Photo Attacks in Face Recognition: a public database and
  a baseline, Anjos & Marcel, IJCB'11.

  This script will output a number of clustered observations containing the 5
  described quantities for windows of a configurable size (N):

    1. The minimum value observed on the cluster
    2. The maximum value observed on the cluster
    3. The mean value observed
    4. The standard deviation on the cluster (unbiased estimator)
    5. The DC ratio (D) as defined by:

  .. math::

    D(N) = \frac{\sum_{i=1}^N{|FFT_i|}}{|FFT_0|}

  .. note::
    
    We always ignore the first entry from the input array as, by definition, it 
    is always zero.
  """

  retval = []
  for k in range(1, arr.shape[0]-window_size+1, window_size-overlap):
    obs = arr[k:k+window_size]
    retval.append((obs.min(), obs.max(), obs.mean(), obs.std(ddof=1),
      dcratio(obs)))
  return retval

def accumulate_5quantities(arr):
  """Calculates the clustered values at every instant T of the input set of
  differences, starting at frame 1 (remember frame 0 is always 0)

  This script will output a number of clustered observations containing the 5
  described quantities for windows of a variable size (V):

    1. The minimum value observed on the cluster
    2. The maximum value observed on the cluster
    3. The mean value observed
    4. The standard deviation on the cluster (unbiased estimator)
    5. The DC ratio (D) as defined by:

  .. math::

    D(V) = \frac{\sum_{i=1}^V{|FFT_i|}}{|FFT_0|}

  .. note::
    
    We always ignore the first entry from the input array as, by definition, it 
    is always zero.
  """

  retval = []
  for k in range(2, arr.shape[0]):
    obs = arr[1:k]
    retval.append((obs.min(), obs.max(), obs.mean(), obs.std(ddof=1),
      dcratio(obs)))
  return retval
