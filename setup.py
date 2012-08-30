#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 16 Apr 08:18:08 2012 CEST

from setuptools import setup, find_packages

def make_single(top):
  """Makes a single RST output by reading the given document and concatenating
  it with its own ..include directives"""
  import re
  regexp = re.compile(r'^\s*..\sinclude::\s*(?P<i>\S+)\s*$')

  output = ''

  for l in open(top, 'rt'):

    match = regexp.match(l)

    if match is not None:
      output += make_single(match.groupdict()['i'])
    else:
      output += l

  return output

# The only thing we do in this file is to call the setup() function with all
# parameters that define our package.
setup(

    name='antispoofing.motion',
    version='1.0.0',
    description='Motion counter-measures for the PRINT-ATTACK database',
    url='http://pypi.python.org/pypi/antispoofing.motion',
    license='GPLv3',
    author='Andre Anjos',
    author_email='andre.anjos@idiap.ch',
    long_description=make_single('README.rst'),

    # This line is required for any distutils based packaging.
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,

    namespace_packages=[
      "antispoofing",
      ],

    install_requires=[
      "setuptools",
      "bob >= 1.0.0, < 1.1.0",
    ],

    entry_points={

      'console_scripts': [
        'framediff.py = antispoofing.motion.script.framediff:main',
        'diffcluster.py = antispoofing.motion.script.diffcluster:main',
        'rproptrain.py = antispoofing.motion.script.rproptrain:main',
        'time_analysis.py = antispoofing.motion.script.time_analysis:main',
        ],

      },

)
