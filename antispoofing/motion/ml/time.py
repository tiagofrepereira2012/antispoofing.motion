#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Tue 23 Aug 08:38:06 2011 

"""Time Analysis performance figures
"""

import os
import bob
import numpy

def scores(flist):
  d = bob.io.load(flist)
  return d[~numpy.isnan(d.sum(axis=1)),:]

def eval_threshold(real, attack, minhter, verbose):
  """Evaluates the optimal threshold for a given MLP/dataset"""
  
  if verbose: 
    print "Establishing optimal separation threshold at development set..."

  real_scores = scores(real)
  attack_scores = scores(attack)

  if minhter:
    thres = bob.measure.min_hter_threshold(attack_scores[:,0], real_scores[:,0])
    if verbose: print "Min. HTER threshold is: %.4e" % thres
  else:
    thres = bob.measure.eer_threshold(attack_scores[:,0], real_scores[:,0])
    if verbose: print "EER threshold is: %.4e" % thres

  return thres

def apply_threshold (value, threshold):
  """Applies a threshold against a certain value"""
  if numpy.isnan(value): return numpy.nan
  if value < threshold: return -1.
  return +1.
  
def threshold_scores(filename, threshold):
  """Returns a vector of decisions given a certain filename, machine and the 
  threshold. These decisions are integers: -1 if it is an attack, 1 if it is a
  real access.

  if score < threshold => is attack, set -1
  if scores >= threshold => is real-access, set +1
  """
  output = bob.io.load(filename)
  return numpy.array([apply_threshold(k, threshold) for k in output])

def average_scores(score, time):
  """Compacts an input vector of decisions into a single value averaging the
  scores upt to a certain time"""
  return score[:time].mean()

def thresholded_running_average(score):
  """Returns a new vector with decisions based on the running average of the
  input scores"""
  retval = numpy.copy(score)
  good = score[~numpy.isnan(score)]
  retval[~numpy.isnan(score)] = [apply_threshold(good[:(k+1)].mean(),0) for k in range(good.size)]
  return retval

def decisions(data, threshold, average=False, verbose=False):
  """Returns a list of booleans (-1, +1) indicating the decisions through time
  for all input data.
  """

  decisions = []
  for filename in data:
    if verbose: print "Scoring file %s..." % filename
    S = bob.io.load(filename)
    if not average: #threshold before
      S = numpy.array([apply_threshold(S[k], threshold) \
          for k in range(len(S))])
    decisions.append(thresholded_running_average(S))
  return decisions

def frfa_list(real, attack, threshold, average=False, verbose=False):
  """Returns a list composed of the false rejections and false accepts"""

  real_decisions = decisions(real, threshold, average, verbose)
  attack_decisions = decisions(attack, threshold, average, verbose)

  # It only makes sense to analyze up to the smallest clip size...
  maxtime = min([len(k) for k in real_decisions] + \
      [len(k) for k in attack_decisions])

  fr = []
  fa = []
  for k in range(0, maxtime):

    fr_k = [] #false rejections for k=k
    real_round = [d[k] for d in real_decisions]
    if numpy.isnan(real_round).all(): fr_k = None
    else: # this is a valid round, process it 
      for i, rd in enumerate(real_round):
        # if the score is NaN, assume it is a real-access
        if not numpy.isnan(rd) and rd < 0: fr_k.append(real[i])

    fa_k = [] #false accepts for k=k
    attack_round = [d[k] for d in attack_decisions]
    if numpy.isnan(attack_round).all(): fa_k = None
    else:
      # if the score is NaN, assume it is a real-access
      for i, ad in enumerate(attack_round):
        if numpy.isnan(ad) or ad >= 0: fa_k.append(attack[i])

    fr.append(fr_k)
    fa.append(fa_k)

  return fr, fa

def instantaneous_decisions(data, threshold, verbose=False):
  """Returns a list of booleans (-1, +1) indicating the decisions through time
  for all input data.
  """

  decisions = []
  for i, filename in enumerate(data):
    if verbose: 
      print "Thresholding file %s [%d/%d]..." % (filename, i+1, len(data))
    S = bob.io.load(filename)
    S = [apply_threshold(k, threshold) for k in S]
    decisions.append(S)
  return decisions

def instantaneous_frfa_list(real, attack, threshold, verbose=False):
  """Returns a list composed of the false rejections and false accepts for
  every instant w/o taking into consideration previous decisions."""

  real_decisions = instantaneous_decisions(real, threshold, verbose)
  attack_decisions = instantaneous_decisions(attack, threshold, verbose)

  # It only makes sense to analyze up to the smallest clip size...
  maxtime = min([len(k) for k in real_decisions] + \
      [len(k) for k in attack_decisions])

  fr = []
  fa = []
  for k in range(0, maxtime):

    fr_k = [] #false rejections for k=k
    real_round = [d[k] for d in real_decisions]
    if numpy.isnan(real_round).all(): fr_k = None
    else: # this is a valid round, process it 
      for i, rd in enumerate(real_round):
        # if the score is NaN, assume it is a real-access
        if not numpy.isnan(rd) and rd < 0: fr_k.append(real[i])

    fa_k = [] #false accepts for k=k
    attack_round = [d[k] for d in attack_decisions]
    if numpy.isnan(attack_round).all(): fa_k = None
    else:
      # if the score is NaN, assume it is a real-access
      for i, ad in enumerate(attack_round):
        if numpy.isnan(ad) or ad >= 0: fa_k.append(attack[i])

    fr.append(fr_k)
    fa.append(fa_k)

  return fr, fa
  
class Analyzer:
  """A class that conducts full time analysis on a set of values"""

  def __init__(self, real_files, attack_files, threshold,
      windowsize, overlap, average, verbose):
    """Initializes the analyzer with the real and attack files for a
    specific protocol, runs the base analysis using the given threshold. If
    average is set, use score averaging instead of instantaneous thresholding.
    """
  
    if verbose: print "Running the time analysis..."

    # calculates the instantaneous lists
    (fr, fa) = instantaneous_frfa_list(real_files, attack_files,
        threshold, verbose)

    self.instd = {}

    for i, (fr, fa) in enumerate(zip(fr, fa)):
      if fr is None and fa is None: continue
      self.instd[i] = {}
      self.instd[i]['frr'] = 100*float(len(fr))/len(real_files)
      self.instd[i]['fr'] = fr
      self.instd[i]['far'] = 100*float(len(fa))/len(attack_files)
      self.instd[i]['fa'] = fa
      self.instd[i]['hter'] = 0.5 * (self.instd[i]['far']+self.instd[i]['frr'])

    # calculates the averaged lists
    (fr, fa) = frfa_list(real_files, attack_files,
        threshold, average, verbose)

    self.d = {}

    for i, (fr, fa) in enumerate(zip(fr, fa)):
      if fr is None and fa is None: continue
      self.d[i] = {}
      self.d[i]['frr'] = 100*float(len(fr))/len(real_files)
      self.d[i]['fr'] = fr
      self.d[i]['far'] = 100*float(len(fa))/len(attack_files)
      self.d[i]['fa'] = fa
      self.d[i]['hter'] = 0.5 * (self.d[i]['far'] + self.d[i]['frr'])

  def write_table(self, file, instantaneous=False):
    """Writes a nicely formatted table containing the time-analysis"""

    use = self.d
    if instantaneous: use = self.instd

    def print_max(value, fmt, maxlength):
      v = fmt % k
      if len(v) > maxlength: maxlength = len(v)
      return v, maxlength

    txt = {}
    max_frame = 0
    max_far = 0
    max_fa = 0
    max_frr = 0
    max_fr = 0
    max_hter = 0
    for k in use.keys():
      txt[k] = {}
      txt[k]['frame'], max_frame = print_max(k, '%d', max_frame)
      txt[k]['frr'], max_frr = print_max(use[k]['frr'], '%.2f%%', max_frr)
      txt[k]['fr'], max_fr = print_max(len(use[k]['fr']), '%d', max_fr)
      txt[k]['far'], max_far = print_max(use[k]['far'], '%.2f%%', max_far)
      txt[k]['fa'], max_fa = print_max(len(use[k]['fa']), '%d', max_fa)
      txt[k]['hter'], max_hter = print_max(use[k]['hter'], '%.2f%%',
        max_hter)

    spacing = 1

    frame_size = max(max_frame, len('Frame'))
    frr_size = max(max_frr, len('FRR'))
    fr_size = max(max_fr, len('#FR'))
    far_size = max(max_far, len('FAR'))
    fa_size = max(max_fa, len('#FA'))
    hter_size = max(max_hter, len('HTER'))

    sizes = [
      (frame_size+2*spacing),
      (frr_size+2*spacing),
      (fr_size+2*spacing),
      (far_size+2*spacing),
      (fa_size+2*spacing),
      (hter_size+2*spacing),
      ]

    hline = [k*'=' for k in sizes]
    header = [
      'Frame'.center(sizes[0]),
      'FRR'.center(sizes[1]),
      '#FR'.center(sizes[2]),
      'FAR'.center(sizes[3]),
      '#FA'.center(sizes[4]),
      'HTER'.center(sizes[5]),
      ]

    file.write(' '.join(hline) + '\n')
    file.write(' '.join(header) + '\n')
    file.write(' '.join(hline) + '\n')

    curr_fr = -1
    curr_fa = -1
    first_time = True
    for k in sorted(use.keys()):
      if curr_fr == len(use[k]['fr']) and curr_fa == len(use[k]['fa']):
        if first_time:
          data = [
            '...'.center(sizes[0]),
            '...'.center(sizes[1]),
            '...'.center(sizes[2]),
            '...'.center(sizes[3]),
            '...'.center(sizes[4]),
            '...'.center(sizes[5]),
            ]
          file.write(' '.join(data) + '\n')
          first_time = False
      else:
        data = [
          ('%d' % k).rjust(sizes[0]-2*spacing).center(sizes[0]),
          ('%.2f%%' % use[k]['frr']).rjust(sizes[1]-2*spacing).center(sizes[1]),
          ('%d' % len(use[k]['fr'])).rjust(sizes[2]-2*spacing).center(sizes[2]),
          ('%.2f%%' % use[k]['far']).rjust(sizes[3]-2*spacing).center(sizes[3]),
          ('%d' % len(use[k]['fa'])).rjust(sizes[4]-2*spacing).center(sizes[4]),
          ('%.2f%%' % use[k]['hter']).rjust(sizes[5]-2*spacing).center(sizes[5]),
          ]
        file.write(' '.join(data) + '\n')

        # reset
        curr_fr = len(use[k]['fr'])
        curr_fa = len(use[k]['fa'])
        first_time = True
    
    file.write(' '.join(hline) + '\n')

  def write_misclassified(self, file, at=None, instantaneous=False):
    """Writes a nicely formatted table containing the misclassified files"""

    use = self.d
    if instantaneous: use = self.instd

    if at is None:
      at = sorted(use.keys())[-1]

    file.write('Misclassified Real-Accesses (FR) at frame %d\n' % at)
    for k in use[at]['fr']: file.write('%s\n' % k)

    file.write('\nMisclassified Attacks (FA) at frame %d\n' % at)
    for k in use[at]['fa']: file.write('%s\n' % k)

  def plot(self, pdffilename, title):
    """Creates a plot showing the FAR, FRR and HTER time evolution"""

    import matplotlib; matplotlib.use('pdf') #avoids TkInter threaded start
    import matplotlib.pyplot as mpl

    x = sorted(self.d.keys())
    far = [self.d[k]['far'] for k in x] 
    frr = [self.d[k]['frr'] for k in x] 
    hter = [self.d[k]['hter'] for k in x] 
    ix = sorted(self.instd.keys())
    ifar = [self.instd[k]['far'] for k in x] 
    ifrr = [self.instd[k]['frr'] for k in x] 
    ihter = [self.instd[k]['hter'] for k in x] 

    mpl.plot(ix, ifar, color='blue', alpha=0.4, dashes=(6,2),
        linestyle='dashed', label='Inst.FAR')
    mpl.plot(ix, ifrr, color='blue', alpha=0.6, linestyle=':', label='Inst.FRR')
    mpl.plot(ix, ihter, color='blue', alpha=0.6, label='Inst.HTER')
    mpl.plot(x, far, color='black', alpha=0.4, dashes=(6,2),
        linestyle='dashed', label='Avg.FAR')
    mpl.plot(x, frr, color='black', linestyle=':', label='Avg.FRR')
    mpl.plot(x, hter, color='black', label='Avg.HTER')
    mpl.title(title)
    mpl.xlabel('Frames')
    mpl.ylabel('Error')
    mpl.grid(True, alpha=0.4)
    mpl.legend()
    mpl.savefig(pdffilename)
