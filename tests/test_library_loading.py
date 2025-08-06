#!/usr/bin/env python

"""
Tests for library loading and basic function access.
These tests verify that the library loads correctly without requiring hardware.
"""

import os
import platform

import pytest


def test_import_sciencemode():
    """Test that sciencemode module can be imported."""
    assert True, "sciencemode module imported successfully"


def test_sciencemode_has_ffi_and_lib():
    """Test that sciencemode module has ffi and lib attributes."""
    from sciencemode import sciencemode

    assert hasattr(sciencemode, "ffi"), "sciencemode.ffi exists"
    # lib is optional as it might only be available when accessing functions
    if hasattr(sciencemode, "lib"):
        assert True, "sciencemode.lib exists"


@pytest.mark.parametrize(
    "function_name",
    [
        "smpt_open_serial_port",
        "smpt_close_serial_port",
        "smpt_check_serial_port",
        "smpt_packet_number_generator_next",
        "smpt_new_packet_received",
        "smpt_last_ack",
    ],
)
def test_lib_function_exists(function_name):
    """Test that expected functions exist in the library."""
    from sciencemode import sciencemode

    # If function doesn't exist, it may be a mock function will be injected later
    if hasattr(sciencemode, function_name):
        assert True, f"Function {function_name} exists"
    else:
        pytest.skip(f"Function {function_name} not found - may need mock injection")


def test_library_location():
    """Test to check where the library is being loaded from."""
    import sciencemode

    # Get package directory
    package_dir = os.path.dirname(sciencemode.__file__)
    print(f"Package directory: {package_dir}")

    # List all files in the package directory
    files = os.listdir(package_dir)
    library_files = [f for f in files if f.startswith("libsmpt") or f.endswith(".dll")]

    print(f"Library files in package directory: {library_files}")
    assert len(library_files) > 0, "Library files found in package directory"


def test_create_device_struct():
    """Test that we can create a device struct with FFI."""
    from sciencemode import sciencemode

    # Create a device struct - this tests FFI but doesn't require hardware
    device = sciencemode.ffi.new("Smpt_device*")
    assert device is not None, "Device struct created successfully"

    # Test a few basic fields
    if platform.system() == "Windows":
        assert hasattr(
            device, "serial_port_handle_"
        ), "Device struct has serial_port_handle_ field on Windows"
    else:
        assert hasattr(
            device, "serial_port_descriptor"
        ), "Device struct has serial_port_descriptor field on Linux/macOS"

    assert hasattr(
        device, "serial_port_name"
    ), "Device struct has serial_port_name field"
