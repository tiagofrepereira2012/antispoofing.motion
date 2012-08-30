.. vim: set fileencoding=utf-8 :
.. Andre Anjos <andre.anjos@idiap.ch>
.. Tue 23 Aug 2011 18:21:16 CEST

===========================
 Frame Difference Workflow
===========================

It is assumed you have followed the installation instructions for the package
and got this package installed and the PRINT-ATTACK database downloaded and
uncompressed in a directory.  You should have all required utilities sitting
inside a binary directory depending on your installation strategy (utilities
will be inside the ``bin`` if you used the buildout option). We expect that the
video files downloaded for the PRINT-ATTACK database are installed in a
sub-directory called ``database`` at the root of the package.  You can use a
link to the location of the database files, if you don't want to have the
database installed on the root of this package::

  $ ln -s /path/where/you/installed/the/print-attack-database database

If you don't want to create a link, use the ``--input-dir`` flag to specify
the root directory containing the database files. That would be the directory
that *contains* the sub-directories ``train``, ``test``, ``devel`` and
``face-locations``.

Calculate Frame Differences
---------------------------

The first stage of the process is to calculate the normalized frame differences
using video sequences. The program that will do that should be sitting in
`bin/framediff.py`. It can calculate normalize frame differences in distinct
parts of the scene (given you provide face locations for each of the frames in
all video sequences to be analyzed).

To execute the frame difference process to all videos in the PRINT-ATTACK
database, just execute::

  $ ./bin/framediff.py

There are more options for the `framediff.py` script you can use. Just type
`--help` at the command line for instructions.

Calculate the 5 Quantities
--------------------------

The second step in calculating the frame differences is to compute the set of 5
quantities that are required for the detection process. To reproduce the
results in the paper, we accumulate the results in windows of 20 frames,
without overlap::

  $ ./bin/diffcluster.py

There are more options for the `diffcluster.py` script you can use. Just type
`--help` at the command line for instructions.

Training an MLP
---------------

Training MLPs to perform discrimination should go like this::

  $ ./bin/rproptrain.py --verbose --epoch=10000 --batch-size=500 --no-improvements=1000000 --maximum-iterations=10000000

This will create a new MLP and train it using the data produced by the
"clustering" step. The training can take anywhere from 20 to 30 minutes (or
even more), depending on your machine speed. You should see some debugging
output with the partial results as the training go along::

  ...
  iteration: RMSE:real/RMSE:attack (EER:%) ( train | devel )
  0: 9.1601e-01/1.0962e+00 (60.34%) | 9.1466e-01/1.0972e+00 (58.71%)
  0: Saving best network so far with average devel. RMSE = 1.0059e+00
  0: New valley stop threshold set to 1.2574e+00
  10000: 5.6706e-01/4.2730e-01 (8.29%) | 7.6343e-01/4.3836e-01 (11.90%)
  10000: Saving best network so far with average devel. RMSE = 6.0089e-01
  10000: New valley stop threshold set to 7.5112e-01
  20000: 5.6752e-01/4.2222e-01 (8.21%) | 7.6444e-01/4.3515e-01 (12.07%)
  20000: Saving best network so far with average devel. RMSE = 5.9979e-01
  20000: New valley stop threshold set to 7.4974e-01

The resulting MLP will be saved in the default output directory called
``window_based``. The resulting directory will also contain performance
analysis plots. The results derived after this step are equivalent to the
results shown at Table 2 and Figure 3 at the paper.

To get results for specific supports as shown at the first two lines of Table
2, just select the support using the ``--support=hand`` or ``--support=fixed``
as a flag to ``rproptrain.py``. At this point, it is adviseable to use
different output directories using the ``--output-dir`` flag as well. If you
need to modify or regenerate Figure 3 at the paper, just look at
`antispoofing/ml/perf.py`, which contains all plotting and analysis routines.

Running the Time Analysis
-------------------------

The time analysis is the end of the processing chain, it fuses the scores of
instantaneous MLP outputs to give out a better estimation of attacks and
real-accesses. To use it::

  $ ./bin/time_analysis.py --network-dir=window_based --feature-dir=clustered --support=hand+fixed

The 3 curves on Figure 4 at the paper relate to the different support types.
Just repeat the procedure for every system trained with data for a particular
support (equivalent for then entries in Table 2). The output for this script is
dumped in PDF (plot) and text (``.rst`` file) on the directory containing the
matching neural net (passed as parameter to ``--network-dir``).

Problems
--------

In case of problems, please contact ``andre.anjos@idiap.ch`` and/or
``sebastien.marcel@idiap.ch``.
