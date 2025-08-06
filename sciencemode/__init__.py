"""
ScienceMode4 Python CFFI wrapper
"""

import os
import sys
import ctypes
from pathlib import Path
from . import sciencemode

# First, try to load the shared library from our package directory


def _find_and_load_library():
    """Find and preload the SMPT library from the package directory"""
    package_dir = os.path.abspath(os.path.dirname(__file__))

    # Define library names based on platform
    if sys.platform.startswith("win"):
        lib_names = ["smpt.dll", "libsmpt.dll"]
    elif sys.platform.startswith("darwin"):  # macOS
        lib_names = ["libsmpt.dylib", "libsmpt.so", "libsmpt.so.4", "libsmpt.so.4.0.0"]
    else:  # Linux/Unix
        lib_names = ["libsmpt.so", "libsmpt.so.4", "libsmpt.so.4.0.0"]

    # Try to load the library from the package directory
    for name in lib_names:
        lib_path = os.path.join(package_dir, name)
        if os.path.exists(lib_path):
            try:
                if sys.platform.startswith("win"):
                    return ctypes.cdll.LoadLibrary(lib_path)
                else:
                    return ctypes.CDLL(lib_path)
            except Exception:
                # Continue to next library if this one fails
                pass

    return None


# Preload the library
_libsmpt = _find_and_load_library()


__all__ = ["sciencemode"]
