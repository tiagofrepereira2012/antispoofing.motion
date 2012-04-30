.. vim: set fileencoding=utf-8 :
.. Andre Anjos <andre.anjos@idiap.ch>
.. Tue 23 Aug 2011 18:21:16 CEST

===========================
 Frame Difference Workflow
===========================

This document explains the frame difference work flow and how to replicate the
results obtained at::

  @INPROCEEDINGS{Anjos_IJCB_2011,
    author = {Anjos, Andr{\'{e}} and Marcel, S{\'{e}}bastien},
    keywords = {Attack, Counter-Measures, Counter-Spoofing, Disguise, Dishonest Acts, Face Recognition, Face Verification, Forgery, Liveness Detection, Replay, Spoofing, Trick},
    month = oct,
    title = {Counter-Measures to Photo Attacks in Face Recognition: a public database and a baseline},
    journal = {International Joint Conference on Biometrics 2011},
    year = {2011},
    pdf = {http://publications.idiap.ch/downloads/papers/2011/Anjos_IJCB_2011.pdf}
  }

It is assumed you have followed the installation instructions for the package,
as described in the ``README.txt`` file located in the root of the package.
After running the ``buildout`` command, you should have all required utilities
sitting inside the ``bin`` directory.

Calculate Frame Differences
---------------------------

The first stage of the process is to calculate the normalized frame differences
using video sequences. The program that will do that should be sitting in
`bin/framediff.py`. It can calculate normalize frame differences in distinct
parts of the scene (given you provide face locations for each of the frames in
all video sequences to be analyzed).

To execute the frame difference process to all videos in the PRINT-ATTACK
database, just execute::

  $ ./bin/framediff.py -p print -f <face-locations-dir>

There are more options for the `framediff.py` script you can use. Just type
`--help` at the command line for instructions.

Calculate the 5 Quantities
--------------------------

The second step in calculating the frame differences is to compute the set of 5
quantities that are required for the detection process. To reproduce the
results in the paper, we accumulate the results in windows of 20 frames,
without overlap::

  $ ./bin/diffcluster.py -v <framediff-basedir> --window-size=20

Training an MLP
---------------

Training MLPs to perform discrimination should go like this::

  $ ./bin/rproptrain.py --verbose --epoch=10000 --batch-size=500 --no-improvements=1000000 --maximum-iterations=10000000 features/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand/rprop-trained

This will create a new MLP and train it using the input data (first directory).
The resulting MLP will be saved in the output directory (second directory). The
resulting directory will also contain performance analysis plots.

Running the Performance Analysis
--------------------------------

It is possible to re-run the performance analysis on a directory containing a
trained MLP by using the `rpropanalyze.py` script. You just need to pass it the
directory containing the trained neural network::

  $ ./bin/rpropanalyze.py --verbose mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand/rprop-trained

Running the Time Analysis
-------------------------

The time analysis is the end of the processing chain, it fuses the scores of
instantaneous MLP outputs to give out a better estimation of attacks and
real-accesses. To use it::

  $ ./bin/time_analysis.py mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_40/overlap_39/face_reminder+eyes+background/print/hand+fixed/run-6133391-7

Omitted parameters will be guessed from the input directory name, if they can,
otherwise an error is raised. To avoid the error, you may add options to
`time_analysis.py` precising the window size used, the overlap, the protocol to
be probed, the supports and the directory containing the features that will be
used for the analysis.
