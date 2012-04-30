#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Tue 19 Jul 2011 12:53:56 CEST 

"""The spooflib contains classes and methods we commonly use for anti-spoofing
in face recognition. The library is heavily based on Bob.
"""

# note: avoid importing like this:
from .framediff import *
from .cluster import *
