# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import glob
import os
from io import FileIO
from pathlib import Path
import platform
import sys
import shutil

VERSION = '1.0.0'

package_data = {'': ['*.xml']}
package_data['sciencemode'] = ['*.dll']
#if sys.platform.startswith('win'):  # windows
#    devel_roots = Path("./smpt/ScienceMode_Library").absolute()
#    if platform.architecture()[0] == '64bit':
#        architecture = 'x64'
#    else:
#        architecture = 'x86'
#    for devel_root in devel_roots:
#        dll_sources = glob.glob(os.sep.join([devel_root, 'lib', architecture, '*.dll']))
#        dll_dest = 'sciencemode'
#        for dll_source in dll_sources:
#            print('Copying {} to {}'.format(dll_source, dll_dest))
#            shutil.copy(dll_source, dll_dest)
#    package_data['sciencemode'] = ['*.dll']

setup(
    name='sciencemode-cffi',
    packages=['sciencemode'],
    package_data=package_data,
    version=VERSION,
    description='CFFI wrapper for SCIENCEMODE',
    author='Holger Nahrstaedt',
    author_email='holger.nahrstaedt@hasomed.de',
    license="MIT",
    url='https://github.com/sciencemode',
    keywords=['sciencemode', 'cffi'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    setup_requires=['cffi>=1.0.0', 'pycparser>=2.14'],
    cffi_modules=[
        '{}:ffi'.format(os.sep.join(['sciencemode', '_cffi.py'])),
    ],
    install_requires=['cffi>=1.0.0']
)