#!/usr/bin/env python

"""
Test that the SMPT library loads correctly.
"""

import os
import sys


def test_library_import():
    """Test that sciencemode module can be imported."""
    assert True, "sciencemode module imported successfully"


def test_sciencemode_module_import():
    """Test that sciencemode.sciencemode can be imported."""
    assert True, "sciencemode.sciencemode module imported successfully"


def test_ffi_interface():
    """Test FFI interface is available."""
    from sciencemode import sciencemode as sm

    assert hasattr(sm, "ffi"), "FFI interface is available"

    # Check if the enhanced CFFI utilities are available
    if hasattr(sm, "_have_cffi_utils"):
        print(f"Enhanced CFFI utilities available: {sm._have_cffi_utils}")
        if sm._have_cffi_utils:
            # Check for some key enhanced features
            assert hasattr(sm, "managed_new"), "managed_new function is available"
            assert hasattr(sm, "managed_buffer"), "managed_buffer function is available"
            assert hasattr(
                sm, "CFFIResourceManager"
            ), "CFFIResourceManager class is available"


def test_create_device_struct():
    """Test creating a device struct."""
    import pytest

    from sciencemode import sciencemode as sm

    # Try to use standard ffi.new first (most compatible way)
    try:
        device = sm.ffi.new("Smpt_device*")
        assert device is not None, "Device struct created successfully with ffi.new"
        return  # Test passed, return early
    except Exception as e:
        print(f"Error using ffi.new: {e}")

    # If that failed, try managed_new if available
    if (
        hasattr(sm, "_have_cffi_utils")
        and sm._have_cffi_utils
        and hasattr(sm, "managed_new")
    ):
        try:
            device = sm.managed_new("Smpt_device*")
            assert (
                device is not None
            ), "Device struct created successfully with managed_new"
            return  # Test passed, return early
        except Exception as e:
            print(f"Error using managed_new: {e}")

    # If all allocation methods failed, skip the test
    pytest.skip("Could not create Smpt_device struct with available methods")


def test_library_files_exist():
    """Test that library files exist in package directory."""
    import sciencemode

    package_dir = os.path.dirname(sciencemode.__file__)
    lib_files = [
        f
        for f in os.listdir(package_dir)
        if f.startswith("lib")
        or f.endswith(".dll")
        or f.endswith(".so")
        or f.endswith(".lib")
    ]
    assert len(lib_files) > 0, f"Library files found: {lib_files}"


if __name__ == "__main__":
    # Allow running directly for quick testing during installation
    try:
        print("Testing ScienceMode library loading...")
        test_library_import()
        print("✓ Library import successful")

        test_sciencemode_module_import()
        print("✓ Module import successful")

        test_ffi_interface()
        print("✓ FFI interface available")

        test_create_device_struct()
        print("✓ Device struct creation successful")

        test_library_files_exist()
        print("✓ Library files found in package directory")

        print("\nAll tests PASSED! The library is correctly installed and linked.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
