"""
Test CFFI struct compatibility across platforms.

This module tests that the Smpt_device struct can be allocated and used
without platform-specific size mismatches. The struct uses flexible
array syntax (...;) to handle platform differences.
"""


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

    # Test 2: Field access - only test explicitly defined fields
    try:
        device.packet_length = 100
        assert device.packet_length == 100
        print("✓ Basic field access works")
    except Exception as e:
        print(f"✗ Failed basic field access: {e}")
        raise AssertionError(f"Failed basic field access: {e}") from e

    # Test 3: Array field access (the packet field)
    try:
        device.packet[0] = 255
        device.packet[1] = 128
        assert device.packet[0] == 255
        assert device.packet[1] == 128
        print("✓ packet array field access works")
    except Exception as e:
        print(f"✗ Failed packet array access: {e}")
        raise AssertionError(f"Failed packet array access: {e}") from e

    # Test 4: Struct size calculation (demonstrates flexible struct works)
    try:
        struct_size = sciencemode.ffi.sizeof("Smpt_device")
        print(f"✓ Smpt_device struct size: {struct_size} bytes")
        assert struct_size > 0, "Struct has positive size"
    except Exception as e:
        print(f"✗ Failed struct size calculation: {e}")
        raise AssertionError(f"Failed struct size calculation: {e}") from e

    # Test 5: Multiple allocations (ensures consistent behavior)
    try:
        devices = []
        for i in range(3):
            dev = sciencemode.ffi.new("Smpt_device*")
            dev.packet_length = i * 100
            devices.append(dev)

        for i, dev in enumerate(devices):
            assert dev.packet_length == i * 100
        print("✓ Multiple device allocations work independently")
    except Exception as e:
        print(f"✗ Failed multiple allocations test: {e}")
        raise AssertionError(f"Failed multiple allocations test: {e}") from e

    print("✓ All Smpt_device struct compatibility tests passed!")
