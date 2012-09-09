====================================================
 Motion-Based Counter-Measures for Spoofing Attacks
====================================================

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

This method was originally conceived to work with the `the PRINT-ATTACK
database <https://www.idiap.ch/dataset/printattack>`_, but has since evolved to
work with the whole of the `the REPLAY-ATTACK database
<https://www.idiap.ch/dataset/replayattack>`_, which is a super-set of the
PRINT-ATTACK database. You are allowed to select protocols in each of the
applications described in this manual. To generate the results for the paper,
just select `print` as protocol option where necessary.

The data used in the paper is publicly available and should be downloaded and
installed **prior** to try using the programs described in this package. Visit
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
    recipe = xbob.buildout:external
    egg-directories=/Users/crazyfox/work/bob/build/lib

User Guide
----------

It is assumed you have followed the installation instructions for the package
and got this package installed and the REPLAY-ATTACK (or PRINT-ATTACK) database
downloaded and uncompressed in a directory to which you have read access.
Through this manual, we will call this directory ``/root/of/database``. That
would be the directory that *contains* the sub-directories ``train``, ``test``,
``devel`` and ``face-locations``.

Note for Grid Users
===================

At Idiap, we use the powerful Sun Grid Engine (SGE) to parallelize our job
submissions as much as we can. At the Biometrics group, we have developed a
`little toolbox <http://pypi.python.org/pypi/gridtk>` that can submit and
manage jobs at the Idiap computing grid through SGE.  If you are at Idiap, you
can download and install this toolset by adding ``gridtk`` at the ``eggs``
section of your ``buildout.cfg`` file, if it is not already there. If you are
not, you still may look inside for tips on automated parallelization of
scripts.

The following sections will explain how to reproduce the paper results in
single (non-gridified) jobs. A note will be given where relevant explaining how
to parallalize the job submission using ``gridtk``.

.. note::

  If you decide to run using the grid at Idiap, please note that our Lustre
  filesystem does not work well with SQLite. So, do **not** run from
  ``/idiap/temp``.

Calculate Frame Differences
===========================

The first stage of the process is to calculate the normalized frame differences
using video sequences. The program that will do that should be sitting in
`bin/framediff.py`. It can calculate normalize frame differences in distinct
parts of the scene (given you provide face locations for each of the frames in
all video sequences to be analyzed).

To execute the frame difference process to all videos in the PRINT-ATTACK
database, just execute::

  $ ./bin/framediff.py /root/of/database results/framediff

There are more options for the `framediff.py` script you can use (such as the
sub-protocol selection). Note that, by default, all applications are tunned to
work with the **whole** of the replay attack database. Just type `--help` at
the command line for instructions.

.. note::

  To parallelize this job, do the following::

    $ ./bin/jman submit --array=1200 ./bin/framediff.py /root/of/database results/framediff --grid

  The `magic` number of `1200` entries can be found by executing::

    $ ./bin/framediff.py --grid-count

  Which just prints the number of jobs it requires for the grid execution.

Calculate the 5 Quantities
==========================

The second step in calculating the frame differences is to compute the set of 5
quantities that are required for the detection process. To reproduce the
results in the paper, we accumulate the results in windows of 20 frames,
without overlap::

  $ ./bin/diffcluster.py results/framediff results/quantities

There are more options for the `diffcluster.py` script you can use (such as the
sub-protocol selection). Just type `--help` at the command line for
instructions.

.. note::

  This job is very fast and normally does not require parallelization. You can
  still do it with::

    $ ./bin/jman submit --array=1200 ./bin/diffcluster.py results/framediff results/quantities --grid

Training an MLP
===============

Training MLPs to perform discrimination should go like this::

  $ ./bin/rproptrain.py --verbose --epoch=10000 --batch-size=500 --no-improvements=1000000 --maximum-iterations=10000000 results/quantities mlp

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

The resulting MLP will be saved in the output directory called
``mlp``. The resulting directory will also contain performance
analysis plots. The results derived after this step are equivalent to the
results shown at Table 2 and Figure 3 at the paper.

To get results for specific supports as shown at the first two lines of Table
2, just select the support using the ``--support=hand`` or ``--support=fixed``
as a flag to ``rproptrain.py``. At this point, it is adviseable to use
different output directories using the ``--output-dir`` flag as well. If you
need to modify or regenerate Figure 3 at the paper, just look at
`antispoofing/ml/perf.py`, which contains all plotting and analysis routines.

.. note::

  If you think that the training is taking too long, you can interrupt it by
  pressing ``CTRL-C``. This will cause the script to quit gracefully and still
  evaluate the best MLP network performance to that point. 

.. note::

  To execute this script in the grid environment, just set the output directory
  to depend on the SGE_TASK_ID environment variable::

    $ ./bin/jman --array=10 ./bin/rproptrain.py --verbose --epoch=10000 --batch-size=500 --no-improvements=1000000 --maximum-iterations=10000000 results/quantities 'mlp.%(SGE_TASK_ID)s'

Running the Time Analysis
=========================

The time analysis is the end of the processing chain, it fuses the scores of
instantaneous MLP outputs to give out a better estimation of attacks and
real-accesses. To use it::

  $ ./bin/time_analysis.py network-directory

The 3 curves on Figure 4 at the paper relate to the different support types.
Just repeat the procedure for every system trained with data for a particular
support (equivalent for then entries in Table 2). The output for this script is
dumped in PDF (plot) and text (``.rst`` file) on the directory containing the
matching neural net you passed as input parameter.

Dumping MLP Scores
==================

You can dump the scores for every input file in the ``clustered`` directory
using the ``make_scores.py`` script::

  $ ./bin/make_scores.py network-directory scores

This should give you the detailed output of the MLP for every input file in the
training, development and test sets. You can use these score files in your
own score analysis routines, for example.

Merging Scores
==============

If you wish to create a single `5-column format file
<http://www.idiap.ch/software/bob/docs/nightlies/last/bob/sphinx/html/measure/index.html?highlight=five_col#bob.measure.load.five_column>`_
by combining this counter-measure scores for every video into a single file
that can be fed to external analysis utilities such as our
`antispoofing.evaluation <http://pypi.python.org/pypi/antispoofing.evaluation>`
package, you should use the script ``merge_scores.py``. You will have to
specify how many of the scores in every video you will want to average and the
input directory containing the scores files that will be merged. 

The output of the program consists of a single 5-column formatted file with the
client identities and scores for **every video** in the input directory. A line
in the output file corresponds to a video from the database. 

You run this program on the output of ``make_scores.py``. So, it should look
like this if you followed the previous example::

  $ ./bin/merge_scores.py scores/train motion-train.txt
  $ ./bin/merge_scores.py scores/devel motion-devel.txt
  $ ./bin/merge_scores.py socres/test motion-test.txt

The above commandline examples will generate 3 files containing the training,
development and test scores, accumulated over each video in the respective
subsets, for input scores in the given input directory.

Problems
--------

In case of problems, please contact any of the authors of the paper.
