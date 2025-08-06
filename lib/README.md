# SMPT Library Directory

This directory is used for the SMPT (ScienceMode) C library files, which are required for the Python wrapper to function.

## Automatic Installation

The recommended way to get the library is to let the setup process build it automatically:

```bash
# On Linux/macOS:
./install.sh

# On Windows:
install.bat
```

## Manual Installation Options

If the automatic build process fails, you have several options:

### Option 1: Build manually with CMake

```bash
mkdir -p build_temp && cd build_temp
cmake ../smpt -DCMAKE_INSTALL_PREFIX=../ -DBUILD_SHARED_LIBS=ON -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=../lib
cmake --build .
```

### Option 2: Download pre-built libraries

For Windows:

1. Download [smpt_windows_static_x86.zip](https://github.com/ScienceMode/ScienceMode4_c_library/releases/download/v4.0.0/smpt_windows_static_x86.zip) from the [ScienceMode4_c_library releases](https://github.com/ScienceMode/ScienceMode4_c_library/releases)
2. Extract the DLL files to this directory

For Linux/macOS:

1. The ScienceMode4 C library source code is already included in the `smpt` directory
2. Build it using the CMake commands listed in Option 1 above
3. Copy the resulting shared objects (_.so files or _.dylib) to this directory

## Expected Files

The following files should be present in this directory after a successful build:

### Windows

- smpt.dll or libsmpt.dll
- smpt.lib or libsmpt.lib (optional, for linking)

### Linux

- libsmpt.so
- libsmpt.so.4
- libsmpt.so.4.0.0

### macOS

- libsmpt.dylib
- libsmpt.4.dylib (optional)
