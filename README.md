# ScienceMode4_python_wrapper

- Python wrapper for the ScienceMode 4 protocol

## Introduction

- sciencemode_cffi is a Python wrapper for the ScienceMode library.
- This Python library has been tested on Windows 64-bit with Anaconda Python and on Linux.
- It uses [cffi](https://cffi.readthedocs.io/) for Python bindings.

## How It Works

This package integrates the SMPT C library directly into the Python package:

1. The SMPT C library is built as a static library using CMake
2. The static library file (libsmpt.a, libsmpt.lib, etc.) is copied into the Python package directory
3. When importing the module, the library is automatically handled via CFFI
4. This eliminates the need for system-wide installation of the library

## Requirements

- CMake (>= 3.10)
- C compiler (GCC, Clang, MSVC, etc.)
- Python 3.x with pip
- CFFI (>= 1.0.0)
- pycparser (>= 2.14)

## Installation

### Manual Installation with Setup.py

You can use the improved setup.py directly, which offers more options:

```bash
# Build just the C library
python setup.py build_lib

# Build with a specific build type
python setup.py build_lib --build-type=Debug

# Install the package with the built library
python setup.py install
```

### Manual CMake Build (Alternative)

Alternatively, you can build the library directly with CMake:

```bash
# Create build directory and build the library
mkdir -p build_temp && cd build_temp
cmake ../smpt -DCMAKE_INSTALL_PREFIX=../ -DBUILD_SHARED_LIBS=OFF -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=../lib
cmake --build .

# Copy the library to the Python package directory
cd ..
cp -f lib/libsmpt.a sciencemode/

# Install the Python package
pip install -e .
```

### Using Pre-built Libraries for Windows

If you prefer to use a pre-built library instead of building with CMake:

1. Install MinGW from [MinGW releases](https://github.com/niXman/mingw-builds-binaries/releases)
   - Adjust path where MinGW is installed in sciencemode/\_cffi.py in line 202: `mingw_path = os.getenv('MINGW_PATH', default='...')`
2. Install [Visual Studio compiler](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
3. Download [smpt_windows_static_x86.zip](https://github.com/ScienceMode/ScienceMode4_c_library/releases/download/v4.0.0/smpt_windows_static_x86.zip) from [ScienceMode4_c_library](https://github.com/ScienceMode/ScienceMode4_c_library)
4. Copy the static library (libsmpt.lib) from the archive to both:
   - the /lib directory
   - the /sciencemode directory (to bundle it with the Python package)

## Running Tests

The package includes pytest tests to verify library loading and linking without requiring hardware. Basic tests are run automatically during installation, but you can run more comprehensive tests manually:

### Running Tests

```bash
# Run the basic test script
python tests/run_unittest.py

# Run all tests with pytest
PYTHONPATH=. pytest tests -v
```

This script performs the essential tests to verify:

1. The library can be imported
2. The FFI interface is available
3. Device structures can be created
4. Library files are present in the package directory

### Test Coverage

The tests verify:

1. That the library can be imported
2. That basic structures and functions are accessible
3. That FFI bindings work correctly
4. That API functions can be called (using mock implementations)

These tests don't require physical hardware and provide confidence that the library is correctly built, linked, and functioning.

## Troubleshooting

If you encounter issues with the installation:

1. Make sure CMake is installed and in your PATH
2. Ensure you have a working C compiler
3. Try building with different options: `python setup.py build_lib --build-type=Debug`
4. Check the lib directory to confirm the SMPT library was built properly
5. Run the tests manually to check for library loading issues
6. Look for detailed error messages in the build output

### Library Not Found Issues

If you encounter issues with the static library, try these solutions:

**Option 1: Copy the static library to your Python package directory:**

```bash
# For Linux/macOS
cp lib/libsmpt.a sciencemode/

# For Windows
cp lib\libsmpt.lib sciencemode\

# Then reinstall
pip install -e .
```

**Option 2: Verify include paths and C compiler setup:**
Check that the include paths in \_cffi.py point to the correct header files and that your C compiler is properly configured.

```bash
# Check that header files are available
ls -la include/ScienceMode4
```

## Building and Installing the Wheel

If you want to create a distributable wheel package that includes the static library:

### Manual Process with Improved Setup

```bash
# Prerequisites
pip install setuptools wheel

# Build the C library first
python setup.py build_lib

# Build the wheel
python setup.py bdist_wheel

# Install the wheel
pip install dist/*.whl
```

## Advanced Build Options

The improved setup.py supports several build options:

```bash
# Specify build type
python setup.py build_lib --build-type=Release  # Options: Debug, Release, RelWithDebInfo, MinSizeRel

# The built library automatically uses multiple CPU cores for parallel building
```

## Platform-Specific Notes

### Windows

- The setup process will attempt to detect MSVC or MinGW compilers
- Static library files (.lib) will be copied to both lib/ and sciencemode/ directories
- Both 32-bit and 64-bit builds are supported

### Linux

- Static library files (.a) will be copied to both lib/ and sciencemode/ directories
- The setup will search for libraries in standard installation directories
- GCC or Clang compilers are supported

### macOS

- Static library files (.a) are used for all builds
- The setup handles macOS-specific build requirements
