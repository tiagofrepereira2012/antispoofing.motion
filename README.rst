Motion-Based Counter-Measures for Face Spoofing Attacks
=======================================================

This package implements the motion-based counter-measure to spoofing attacks to
face recognition systems as described at the paper::

  @INPROCEEDINGS{Anjos_IJCB_2011,
    author = {Anjos, Andr{\'{e}} and Marcel, S{\'{e}}bastien},
    keywords = {Attack, Counter-Measures, Counter-Spoofing, Disguise, Dishonest Acts, Face Recognition, Face Verification, Forgery, Liveness Detection, Replay, Spoofing, Trick},
    month = oct,
    title = {Counter-Measures to Photo Attacks in Face Recognition: a public database and a baseline},
    journal = {International Joint Conference on Biometrics 2011},
    year = {2011},
    pdf = {http://publications.idiap.ch/downloads/papers/2011/Anjos_IJCB_2011.pdf}
  }

The data used in the paper is publicly available and should be downloaded and
installed **prior** to try using the programs described in this package. Visit
`the PRINT-ATTACK database page <https://www.idiap.ch/dataset/printattack>`_ for more information.

To run the code in this package, you will also need `Bob, an open-source
toolkit for Signal Processing and Machine Learning
<http://idiap.github.com/bob>`_. The code has been tested to work with Bob
1.0.x.

Installation
------------

To follow these instructions locally you will need a local copy of this
package. Start by cloning this project with something like::

  $ git clone --depth=1 https://github.com/bio.idiap/motion.antispoofing.git
  $ cd bob.project.example
  $ rm -rf .git # you don't need the git directories...

Alternatively, you can use the github tarball API to download the package::

  $ wget --no-check-certificate https://github.com/idiap/bob.project.example/tarball/master -O- | tar xz 
  $ mv idiap-bob.project* bob.project.example

Installation of the toolkit uses the `buildout <http://www.buildout.org/>`_
build environment. You don't need to understand its inner workings to use this
package. Here is a recipe to get you started (shell commands are marked with a
``$`` signal)::
  
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
  else on a private directory, edit the file ``localbob.cfg`` and use that
  with ``buildout`` instead::

    $ python boostrap.py
    $ # edit localbob.cfg
    $ ./bin/buildout -c localbob.cfg

Usage
-----

Please refer to the documentation inside the ``doc`` directory of this package
for further instructions on the functionality available.

Reference
---------

If you need to cite this work, please use the following::

  @INPROCEEDINGS{Anjos_IJCB_2011,
    author = {Anjos, Andr{\'{e}} and Marcel, S{\'{e}}bastien},
    keywords = {Attack, Counter-Measures, Counter-Spoofing, Disguise, Dishonest Acts, Face Recognition, Face Verification, Forgery, Liveness Detection, Replay, Spoofing, Trick},
    month = oct,
    title = {Counter-Measures to Photo Attacks in Face Recognition: a public database and a baseline},
    journal = {International Joint Conference on Biometrics 2011},
    year = {2011},
    pdf = {http://publications.idiap.ch/downloads/papers/2011/Anjos_IJCB_2011.pdf}
  }
