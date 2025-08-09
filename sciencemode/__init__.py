"""
ScienceMode4 Python CFFI wrapper
"""

import os
import sys
import ctypes
from pathlib import Path

# Import the main CFFI functionality
from . import sciencemode


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

# Import CFFI wrapper components and expose them at package level
try:
    # Try to import the CFFI-generated module
    from ._sciencemode import lib, ffi

    # Expose the CFFI library and FFI objects
    lib = lib
    ffi = ffi

    # Create convenience functions for common structures
    def new_device():
        """Create a new Smpt_device structure"""
        return ffi.new("Smpt_device *")

    def new_ll_init():
        """Create a new Smpt_ll_init structure"""
        return ffi.new("Smpt_ll_init *")

    def new_ll_channel_config():
        """Create a new Smpt_ll_channel_config structure"""
        return ffi.new("Smpt_ll_channel_config *")

    def new_ml_init():
        """Create a new Smpt_ml_init structure"""
        return ffi.new("Smpt_ml_init *")

    def new_ml_update():
        """Create a new Smpt_ml_update structure"""
        return ffi.new("Smpt_ml_update *")

    # Expose commonly used enums and constants
    # These will be available directly as attributes
    try:
        # Result codes
        Smpt_Result_Successful = lib.Smpt_Result_Successful
        Smpt_Result_Unsuccessful = lib.Smpt_Result_Unsuccessful

        # Channel numbers
        Smpt_Channel_Red = lib.Smpt_Channel_Red
        Smpt_Channel_Blue = lib.Smpt_Channel_Blue
    except AttributeError:
        # If these specific constants aren't available, that's okay
        pass

    # Add commonly used structures as constructors
    try:
        # Make structures available as direct constructors
        def Smpt_device():
            return ffi.new("Smpt_device *")

        def Smpt_ll_init():
            return ffi.new("Smpt_ll_init *")

        def Smpt_ll_channel_config():
            return ffi.new("Smpt_ll_channel_config *")

        def Smpt_ml_init():
            return ffi.new("Smpt_ml_init *")

        def Smpt_ml_update():
            return ffi.new("Smpt_ml_update *")

    except Exception:
        # If any structure creation fails, define minimal fallbacks
        pass

    # Export main functionality
    __all__ = [
        "lib",
        "ffi",
        "sciencemode",
        "new_device",
        "new_ll_init",
        "new_ll_channel_config",
        "new_ml_init",
        "new_ml_update",
        "Smpt_device",
        "Smpt_ll_init",
        "Smpt_ll_channel_config",
        "Smpt_ml_init",
        "Smpt_ml_update",
    ]

    # Add result constants if available
    if "Smpt_Result_Successful" in locals():
        __all__.extend(["Smpt_Result_Successful", "Smpt_Result_Unsuccessful"])

    # Add channel constants if available
    if "Smpt_Channel_Red" in locals():
        __all__.extend(["Smpt_Channel_Red", "Smpt_Channel_Blue"])

except ImportError as e:
    # If CFFI module is not available, provide a minimal interface
    print(f"Warning: CFFI module not available: {e}")
    print("You may need to rebuild the CFFI module.")

    # Still export the sciencemode module for basic functionality
    __all__ = ["sciencemode"]
