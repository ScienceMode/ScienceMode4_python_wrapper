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
Mingw 5.3 from Qt needs to be installed in `C:\Qt\Tools\mingw530_32`. The [Visual studio compiler](https://visualstudio.microsoft.com/visual-cpp-build-tools/) needs also be installed.

The QT-Binaries can be installed using the [QT Online Installer](https://www.qt.io/download-open-source).

The following should be selected for building the python wheels:
![image](https://github.com/user-attachments/assets/e5559f5b-6973-4cfe-a690-27af627d5e78)



## Install the wheel pacakge
```
pip install wheel
```
## Copy Library to lib
* Download [smpt_windows_static_x86.zip](https://github.com/ScienceMode/ScienceMode4_c_library/releases/download/v4.0.0/smpt_windows_static_x86.zip) from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library)
* copy libsmpt.lib from the smpt_windows_static_x86.zip  to /lib (path inside the zip file is .\ScienceMode_Library\release\smpt\windows_x86\static)

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
