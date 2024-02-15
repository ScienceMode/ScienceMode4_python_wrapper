# ScienceMode4_python_wrapper
Python wrapper for the ScienceMode 4 protocol

## Introduction 

sciencemode_cffi is a python wrapper for the sciencemode library.

This python library was tested on Windows 64bit together with Anaconda Python.

This library is using [cffi](https://cffi.readthedocs.io/).

## Preparation
Unzip the correct version of the smpt library and copy the lib  into the lib directory.
On Windows, build artifacts from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library) can be used.

## How to build for Windows
Mingw 5.3 from Qt needs to be installed in `C:\Qt\Tools\mingw530_32`. Visual studio compiler needs also be installed.

## Install the wheel pacakge
```
pip install wheel
```
## Copy Library to lib
* Download smpt_windows_static_x86.zip from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library)
* copy libsmpt.lib (from ScienceMode_Library\release\smpt\windows_x86\static) from the smpt_windows_static_x86.zip file to /lib
* There should now be a file libsmpt.lib in lib

## Building the wheel
Create a wheel with
```
python setup.py bdist_wheel --universal
```
## Installing the wheel
You may correct the filename, check that the python version is matching the version in the filename.
E.g. for python 3.9, the following version is valid:
```
pip install dist/sciencemode4_cffi-1.0.0-cp39-cp39-win_amd64.whl
```