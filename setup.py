#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 16 Apr 08:18:08 2012 CEST

from setuptools import setup, find_packages

# The only thing we do in this file is to call the setup() function with all
# parameters that define our package.
setup(

    name='antispoofing.motion',
    version='1.0',
    description='Motion counter-measures for the PRINT-ATTACK database',
    url='http://github.com/bioidiap/antispoofing.motion',
    license='LICENSE.txt',
    author_email='Andre Anjos <andre.anjos@idiap.ch>',
    #long_description=open('doc/long-description.rst').read(),

    # This line is required for any distutils based packaging.
    packages=find_packages(),

    install_requires=[
        "bob",      # base signal proc./machine learning library
        "argparse", # better option parsing
    ],

    entry_points={
      'console_scripts': [
        'framediff.py = antispoofing.motion.script.framediff:main',
        'diffcluster.py = antispoofing.motion.script.diffcluster:main',
        'rproptrain.py = antispoofing.motion.script.rproptrain:main',
        'rpropanalyze.py = antispoofing.motion.script.rpropanalyze:main',
        'time_analysis.py = antispoofing.motion.script.time_analysis:main',
        ],
      },

)
