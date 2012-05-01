#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Tue 23 Aug 08:38:06 2011 

"""Time Analysis performance figures
"""

import os
import bob
import numpy
from . import pack

def eval_threshold(inputdir, protocol, support, minhter, verbose):
  """Evaluates the optimal threshold for a given MLP/dataset"""
  
  if verbose: 
    print "Establishing optimal separation threshold at development set..."

  datadir = os.path.join(inputdir, 'dataset')
  machfile = os.path.join(inputdir, 'mlp.hdf5')

  data = pack.replay([datadir], protocol, support, groups=('devel',),
    cls=('attack','real'))

  real = data['devel']['real']
  attack = data['devel']['attack']
  machine = bob.machine.MLP(bob.io.HDF5File(machfile))

  # pass the input data through the machine
  real_scores = machine(real)
  attack_scores = machine(attack)

  if minhter:
    thres = bob.measure.min_hter_threshold(attack_scores[:,0], real_scores[:,0])
    if verbose: print "Min. HTER threshold is: %.4e" % thres
  else:
    thres = bob.measure.eer_threshold(attack_scores[:,0], real_scores[:,0])
    if verbose: print "EER threshold is: %.4e" % thres

  return thres

def scores(filename, machine):
  """Returns a vector of scores given a certain filename and a machine"""
  data = bob.io.load(filename)
  return machine(data)[:,0]

def apply_threshold (value, threshold):
  """Applies a threshold against a certain value"""

  if value < threshold: return -1.
  return +1.
  
def threshold_scores(filename, machine, threshold):
  """Returns a vector of decisions given a certain filename, machine and the 
  threshold. These decisions are integers: -1 if it is an attack, 1 if it is a
  real access.

  if score < threshold => is attack, set -1
  if scores >= threshold => is real-access, set +1
  """
  output = scores(filename, machine)
  return numpy.array([apply_threshold(data[k], threshold) for k in range(data.shape[0])])

def average_scores(score, time):
  """Compacts an input vector of decisions into a single value averaging the
  scores upt to a certain time"""
  return score[:time].mean()

def thresholded_running_average(score):
  """Returns a new vector with decisions based on the running average of the
  input scores"""
  return [apply_threshold(score[:(k+1)].mean(),0) for k in range(score.size)]

def decisions(data, machine, threshold, average=False, verbose=False):
  """Returns a list of booleans (-1, +1) indicating the decisions through time
  for all input data.
  """

  decisions = []
  for filename in data:
    if verbose: print "Scoring file %s..." % filename
    S = scores(filename, machine)
    if not average: #threshold before
      S = numpy.array([apply_threshold(S[k], threshold) \
          for k in range(S.size)])
    decisions.append(thresholded_running_average(S))
  return decisions

def frfa_list(real, attack, machine, threshold, average=False, verbose=False):
  """Returns a list composed of the false rejections and false accepts"""

  real_decisions = decisions(real, machine, threshold, average, verbose)
  attack_decisions = decisions(attack, machine, threshold, average, verbose)

  # It only makes sense to analyze up to the smallest clip size...
  maxtime = min([len(k) for k in real_decisions] + \
      [len(k) for k in attack_decisions])

  fr = []
  fa = []
  for k in range(0, maxtime):
    fr_k = [] #false rejections for k=k
    for i, rd in enumerate(real_decisions):
      if rd[k] < 0: fr_k.append(real[i])
    fa_k = [] #false accepts for k=k
    for i, ad in enumerate(attack_decisions):
      if ad[k] >= 0: fa_k.append(attack[i])
    fr.append(fr_k)
    fa.append(fa_k)

  return fr, fa
  
def instantaneous_decisions(data, machine, threshold, verbose=False):
  """Returns a list of booleans (-1, +1) indicating the decisions through time
  for all input data.
  """

  decisions = []
  for filename in data:
    if verbose: print "Scoring file %s..." % filename
    S = scores(filename, machine)
    S = [apply_threshold(S[k], threshold) for k in range(S.size)]
    decisions.append(S)
  return decisions

def instantaneous_frfa_list(real, attack, machine, threshold, verbose=False):
  """Returns a list composed of the false rejections and false accepts for
  every instant w/o taking into consideration previous decisions."""

  real_decisions = instantaneous_decisions(real, machine, threshold, verbose)
  attack_decisions = instantaneous_decisions(attack, machine, threshold, verbose)

  # It only makes sense to analyze up to the smallest clip size...
  maxtime = min([len(k) for k in real_decisions] + \
      [len(k) for k in attack_decisions])

  fr = []
  fa = []
  for k in range(0, maxtime):
    fr_k = [] #false rejections for k=k
    for i, rd in enumerate(real_decisions):
      if rd[k] < 0: fr_k.append(real[i])
    fa_k = [] #false accepts for k=k
    for i, ad in enumerate(attack_decisions):
      if ad[k] >= 0: fa_k.append(attack[i])
    fr.append(fr_k)
    fa.append(fa_k)

  return fr, fa
  
class Analyzer:
  """A class that conducts full time analysis on a set of values"""

  def __init__(self, real_files, attack_files, machfile, threshold,
      windowsize, overlap, average, verbose):
    """Initializes the analyzer with the real and attack files for a
    specific protocol, runs the base analysis using the machine and the
    given threshold. If average is set, use score averaging instead of
    instantaneous thresholding.
    """
  
    if verbose: print "Running the time analysis..."
    machine = bob.machine.MLP(bob.io.HDF5File(machfile))

    # calculates the instantaneous lists
    (fr, fa) = instantaneous_frfa_list(real_files, attack_files,
        machine, threshold, verbose)

    self.instd = {}

    for i, (fr, fa) in enumerate(zip(fr, fa)):
      realtime = (i*(windowsize-overlap)) + windowsize
      self.instd[realtime] = {}
      self.instd[realtime]['frr'] = 100*float(len(fr))/len(real_files)
      self.instd[realtime]['fr'] = fr
      self.instd[realtime]['far'] = 100*float(len(fa))/len(attack_files)
      self.instd[realtime]['fa'] = fa
      self.instd[realtime]['hter'] = 0.5 * (self.instd[realtime]['far'] + \
          self.instd[realtime]['frr'])

    # calculates the averaged lists
    (fr, fa) = frfa_list(real_files, attack_files,
        machine, threshold, average, verbose)

    self.d = {}

    for i, (fr, fa) in enumerate(zip(fr, fa)):
      realtime = (i*(windowsize-overlap)) + windowsize
      self.d[realtime] = {}
      self.d[realtime]['frr'] = 100*float(len(fr))/len(real_files)
      self.d[realtime]['fr'] = fr
      self.d[realtime]['far'] = 100*float(len(fa))/len(attack_files)
      self.d[realtime]['fa'] = fa
      self.d[realtime]['hter'] = 0.5 * (self.d[realtime]['far'] + \
          self.d[realtime]['frr'])

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
