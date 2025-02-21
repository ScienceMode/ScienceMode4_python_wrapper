# ScienceMode4_python_wrapper
* Python wrapper for the ScienceMode 4 protocol

## Introduction 
* sciencemode_cffi is a python wrapper for the sciencemode library.
* This python library was tested on Windows 64bit together with Anaconda Python.
* This library is using [cffi](https://cffi.readthedocs.io/).

## Preparation
* Unzip the correct version of the smpt library and copy the lib  into the lib directory.
* On Windows, build artifacts from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library) can be used.

## Copy Library to lib
* Download [smpt_windows_static_x86.zip](https://github.com/ScienceMode/ScienceMode4_c_library/releases/download/v4.0.0/smpt_windows_static_x86.zip) from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library)
* copy libsmpt.lib from the smpt_windows_static_x86.zip  to /lib (path inside the zip file is .\ScienceMode_Library\release\smpt\windows_x86\static)

## How to build for Windows
* Install MinGW from [MinGW releases](https://github.com/niXman/mingw-builds-binaries/releases)
  * Adjust path where MinGW is installed in ScienceMode/_cffi.py in line 202: mingw_path = os.getenv('MINGW_PATH', default='...')
* Install [Visual studio compiler](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

## Install setuptools
```
pip install setuptools
```

## Install the wheel pacakge
```
pip install wheel
```

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
