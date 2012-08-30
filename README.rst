============================================================
 Motion-Based Counter-Measures for Printed Spoofing Attacks
============================================================

This package implements a motion-based counter-measure to spoofing attacks to
face recognition systems as described at the paper `Counter-Measures to Photo
Attacks in Face Recognition: a public database and a baseline`, by Anjos and
Marcel, International Joint Conference on Biometrics, 2011.

If you use this package and/or its results, please cite the following
publications:

1. The original paper with the counter-measure explained in details::

    @inproceedings{Anjos_IJCB_2011,
      author = {Anjos, Andr{\'{e}} and Marcel, S{\'{e}}bastien},
      keywords = {Attack, Counter-Measures, Counter-Spoofing, Disguise, Dishonest Acts, Face Recognition, Face Verification, Forgery, Liveness Detection, Replay, Spoofing, Trick},
      month = oct,
      title = {Counter-Measures to Photo Attacks in Face Recognition: a public database and a baseline},
      journal = {International Joint Conference on Biometrics 2011},
      year = {2011},
      pdf = {http://publications.idiap.ch/downloads/papers/2011/Anjos_IJCB_2011.pdf}
    }

2. Bob as the core framework used to run the experiments::

    @inproceedings{Anjos_ACMMM_2012,
        author = {A. Anjos AND L. El Shafey AND R. Wallace AND M. G\"unther AND C. McCool AND S. Marcel},
        title = {Bob: a free signal processing and machine learning toolbox for researchers},
        year = {2012},
        month = oct,
        booktitle = {20th ACM Conference on Multimedia Systems (ACMMM), Nara, Japan},
        publisher = {ACM Press},
    }

If you wish to report problems or improvements concerning this code, please
contact the authors of the above mentioned papers.

Raw data
--------

The data used in the paper is publicly available and should be downloaded and
installed **prior** to try using the programs described in this package. Visit
`the PRINT-ATTACK database portal <https://www.idiap.ch/dataset/printattack>`_
for more information.

Installation
------------

.. note:: 

  If you are reading this page through our GitHub portal and not through PyPI,
  note **the development tip of the package may not be stable** or become
  unstable in a matter of moments.

  Go to `http://pypi.python.org/pypi/antispoofing.motion
  <http://pypi.python.org/pypi/antispoofing.motion>`_ to download the latest
  stable version of this package.

There are 2 options you can follow to get this package installed and
operational on your computer: you can use automatic installers like `pip
<http://pypi.python.org/pypi/pip/>`_ (or `easy_install
<http://pypi.python.org/pypi/setuptools>`_) or manually download, unpack and
use `zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ to create a
virtual work environment just for this package.

Using an automatic installer
============================

Using ``pip`` is the easiest (shell commands are marked with a ``$`` signal)::

  $ pip install antispoofing.motion

You can also do the same with ``easy_install``::

  $ easy_install antispoofing.motion

This will download and install this package plus any other required
dependencies. It will also verify if the version of Bob you have installed
is compatible.

This scheme works well with virtual environments by `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_ or if you have root access to your
machine. Otherwise, we recommend you use the next option.

Using ``zc.buildout``
=====================

Download the latest version of this package from `PyPI
<http://pypi.python.org/pypi/antispoofing.motion>`_ and unpack it in your
working area. The installation of the toolkit itself uses `buildout
<http://www.buildout.org/>`_. You don't need to understand its inner workings
to use this package. Here is a recipe to get you started::
  
  $ python bootstrap.py 
  $ ./bin/buildout

These 2 commands should download and install all non-installed dependencies and
get you a fully operational test and development environment.

.. note::

  The python shell used in the first line of the previous command set
  determines the python interpreter that will be used for all scripts developed
  inside this package. Because this package makes use of `Bob
  <http://idiap.github.com/bob>`_, you must make sure that the ``bootstrap.py``
  script is called with the **same** interpreter used to build Bob, or
  unexpected problems might occur.

  If Bob is installed by the administrator of your system, it is safe to
  consider it uses the default python interpreter. In this case, the above 3
  command lines should work as expected. If you have Bob installed somewhere
  else on a private directory, edit the file ``buildout.cfg`` **before**
  running ``./bin/buildout``. Find the section named ``external`` and edit the
  line ``egg-directories`` to point to the ``lib`` directory of the Bob
  installation you want to use. For example::

    [external]
    egg-directories=/Users/crazyfox/work/bob/build/lib

User Guide
----------

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
===========================

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
==========================

The second step in calculating the frame differences is to compute the set of 5
quantities that are required for the detection process. To reproduce the
results in the paper, we accumulate the results in windows of 20 frames,
without overlap::

  $ ./bin/diffcluster.py

There are more options for the `diffcluster.py` script you can use. Just type
`--help` at the command line for instructions.

Training an MLP
===============

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
=========================

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

In case of problems, please contact any of the authors of the paper.
