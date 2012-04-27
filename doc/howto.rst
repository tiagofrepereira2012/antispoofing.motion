.. vim: set fileencoding=utf-8 :
.. Andre Anjos <andre.anjos@idiap.ch>
.. Tue 23 Aug 2011 18:21:16 CEST

===========================
 Frame Difference Workflow
===========================

This document explains the frame difference work flow and how to replicate the
results obtained on published articles.

Calculate Frame Differences
---------------------------

The first stage of the process is to calculate the normalized frame differences
using video sequences. The program to be used is `script/framediff.py`. It can
calculate normalize frame differences in distinct parts of the scene (given you
provide face locations for each of the frames in all video sequences to be
analyzed).

To execute the frame difference process to all videos in the replay attack
database, just execute:

.. code-block:: shell

  ./shell.py ./script/framediff.py -f <face-locations-dir>

To calculate the framediffs for a specific file on the replay attack database:

.. code-block:: shell

  ./shell.py ./script/framediff.py -i 55 -f <face-locations-dir>

The file numbers can be retrieved using torch's `dbmanage.py` script:

.. code-block:: shell

  ./shell.py dbmanage.py replay reverse <path-to-replay-file>

There are more options for the `framediff.py` script you can use. Just type
`--help` at the command line for instructions.

Calculate the 5 Quantities
--------------------------

The second step in calculating the frame differences is to compute the set of 5
quantities that are required for the detection process. You can calculate these
quantities using different strategies.

Strategy 1: Accumulate
======================

[We don't use these!]

The first option is to accumulate frame differences as time passes and use all
accumulated values to calculate the statistics needed for the 5 quantities. To
do this, use the script `script/diffacc.py`:

.. code-block:: shell

  ./shell.py ./script/diffacc.py -v <framediff-basedir>

The previous instruction will run through the whole database. Use the `-i` flag
to execute the script only for a single file.

Strategy 2: Cluster in Windows
==============================

[Use this]

You can also cluster the observations in groups of `N` frames overlapped by `O`
frames (_math::`O < N`). To do this, use the script `script/diffcluster.py`:

.. code-block:: shell

  ./shell.py ./script/diffcluster.py -v <framediff-basedir> --window-size=20 --overlap=19

Again, to execute the pre-processing with a single file use the `-i` option.

.. note::

  A fast submit script is ready at ``script/grid_make_features.sh`` and will
  submit through the SGE Idiap grid the creation of all features. This about
  66'000 jobs with the currently set configurations.

Cluster data in training, development and testing sets
------------------------------------------------------

After calculating the 5 quantities, possibly from different RoIs, you should
use the Replay attack protocol to cluster the features into Arraysets that
contain data for training, development and testing the discriminators. To do
this you must do something along these lines:

.. code-block:: shell

  ./shell.py ./script/featpack.py --base-dir=features/NoLightNormalization/KeyLemonFaceDetector/5features/accumulated --protocol=photo --support=all face_reminder eyes background

This would create the training, development and testing datasets for the
features in the given base directory using the "photo" protocol with data using
any support type, coming from the face_reminder, the eyes and the background.
Each job should produce 6 arrayset files containing the real-accesses and
attacks for each of the 3 protocolar groups: training, development and testing.

.. note::

  A fast submit script is ready at ``script/grid_make_features.sh`` and will
  execute all clustering you need for all previously calculated features. Edit
  it to make changes if required. This is about 1'440 jobs with the currently
  set configurations.

Training an MLP
---------------

Training MLPs to perform discrimination should go like this:

.. code-block:: shell

  ./shell.py ./script/rproptrain.py --verbose --epoch=10000 --batch-size=500 --no-improvements=1000000 --maximum-iterations=10000000 features/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand/rprop-trained

This will create a new MLP and train it using the input data (first directory).
The resulting MLP will be saved in the output directory (second directory). The
resulting directory will also contain performance analysis plots.

Running the Performance Analysis
--------------------------------

It is possible to re-run the performance analysis on a directory containing a
trained MLP by using the `rpropanalyze.py` script. You just need to pass it the
directory containing the trained neural network:

.. code-block:: shell

  ./shell.py ./script/rpropanalyze.py --verbose mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_20/overlap_19/full/print/hand/rprop-trained

Running the Time Analysis
-------------------------

The time analysis is the end of the processing chain, it fuses the scores of
instantaneous MLP outputs to give out a better estimation of attacks and
real-accesses. To use it:

.. code-block:: shell

  ./shell.py time_analysis.py mlp-results/NoLightNormalization/KeyLemonFaceDetector/5features/window_40/overlap_39/face_reminder+eyes+background/print/hand+fixed/run-6133391-7

Omitted parameters will be guessed from the input directory name, if they can,
otherwise an error is raised. To avoid the error, you may add options to
`time_analysis.py` precising the window size used, the overlap, the protocol to
be probed, the supports and the directory containing the features that will be
used for the analysis.
