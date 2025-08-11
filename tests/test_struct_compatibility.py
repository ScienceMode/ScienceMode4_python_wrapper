#!/usr/bin/env python

"""
Standalone test for Smpt_device struct size compatibility.

This test specifically validates the fix for the CFFI struct size mismatch error:
"ffi.error: Smpt_device: wrong size for field 'packet' (cdef says X, but C
compiler says Y)"

The fix uses flexible struct syntax (...;) in the cdef to handle platform differences.
"""

import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def test_struct_size_compatibility():
    """Test that Smpt_device struct can be created without size mismatches."""
    print("=== Testing Smpt_device Struct Size Compatibility ===")

    try:
        from unittest.mock import MagicMock

        from sciencemode import sciencemode

        print("✓ Successfully imported sciencemode")
    except Exception as e:
        print(f"✗ Failed to import sciencemode: {e}")
        raise AssertionError(f"Failed to import sciencemode: {e}") from e

    # Skip test if sciencemode is mocked (happens on Windows CI)
    if isinstance(sciencemode.ffi, MagicMock):
        import pytest

        pytest.skip("Skipping CFFI struct test - sciencemode module is mocked")

    # Test 1: Basic struct allocation
    try:
        device = sciencemode.ffi.new("Smpt_device*")
        print("✓ Basic Smpt_device* allocation succeeded")
    except Exception as e:
        print(f"✗ Failed to allocate Smpt_device*: {e}")
        raise AssertionError(f"Failed to allocate Smpt_device*: {e}") from e

    # Test 2: Field access
    try:
        device.packet_length = 100
        device.current_packet_number = 42
        assert device.packet_length == 100
        assert device.current_packet_number == 42
        print("✓ Basic field access works")
    except Exception as e:
        print(f"✗ Failed basic field access: {e}")
        raise AssertionError(f"Failed basic field access: {e}") from e

    # Test 3: Array field access (the problematic 'packet' field)
    try:
        device.packet[0] = 255
        device.packet[1] = 128
        assert device.packet[0] == 255
        assert device.packet[1] == 128
        print("✓ Packet array field access works (size mismatch fixed)")
    except Exception as e:
        print(f"✗ Failed packet array access: {e}")
        raise AssertionError(f"Failed packet array access: {e}") from e

    # Test 4: String field access
    try:
        test_name = b"test_port_name"
        sciencemode.ffi.memmove(device.serial_port_name, test_name, len(test_name))
        read_back = sciencemode.ffi.string(device.serial_port_name, len(test_name))
        assert read_back == test_name
        print("✓ String field access works")
    except Exception as e:
        print(f"✗ Failed string field access: {e}")
        raise AssertionError(f"Failed string field access: {e}") from e

    # Test 5: Struct size calculation
    try:
        struct_size = sciencemode.ffi.sizeof("Smpt_device")
        print(f"✓ Smpt_device struct size: {struct_size} bytes")
    except Exception as e:
        print(f"✗ Failed to calculate struct size: {e}")
        raise AssertionError(f"Failed to calculate struct size: {e}") from e

    # Test 6: Multiple allocations
    try:
        devices = []
        for i in range(3):
            dev = sciencemode.ffi.new("Smpt_device*")
            dev.current_packet_number = i
            devices.append(dev)

        for i, dev in enumerate(devices):
            assert dev.current_packet_number == i
        print("✓ Multiple device allocations work independently")
    except Exception as e:
        print(f"✗ Failed multiple allocations test: {e}")
        raise AssertionError(f"Failed multiple allocations test: {e}") from e

    print("\n=== All Struct Compatibility Tests Passed! ===")
    print(
        "The flexible struct fix (using '...;') successfully resolved the size "
        "mismatch issue."
    )


def standalone_test():
    """Standalone version that returns boolean for script execution."""
    try:
        test_struct_size_compatibility()
        return True
    except AssertionError:
        return False


if __name__ == "__main__":
    success = standalone_test()
    sys.exit(0 if success else 1)
