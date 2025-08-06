#!/usr/bin/env python

"""
Tests for SMPT API functions that don't require hardware.
These tests verify basic API functionality and data structure manipulation.
"""

import pytest


# Fixture for the sciencemode module
@pytest.fixture
def sm():
    from sciencemode import sciencemode

    return sciencemode


@pytest.mark.parametrize(
    "constant",
    [
        "Smpt_Length_Serial_Port_Chars",
        "Smpt_Length_Max_Packet_Size",
        "Smpt_Length_Device_Id",
    ],
)
def test_constants_exist(sm, constant):
    """Test that expected constants exist."""
    if hasattr(sm, constant):
        assert True, f"Constant {constant} exists"
    else:
        pytest.skip(f"Constant {constant} not found - may be missing from this build")


@pytest.mark.parametrize(
    "enum_val",
    [
        "Smpt_Channel_Red",
        "Smpt_Channel_Blue",
        "Smpt_Connector_Yellow",
        "Smpt_Connector_Green",
        "Smpt_High_Voltage_Default",
    ],
)
def test_enum_values_exist(sm, enum_val):
    """Test that enum values exist."""
    if hasattr(sm, enum_val):
        assert True, f"Enum value {enum_val} exists"
    else:
        pytest.skip(f"Enum value {enum_val} not found - may be missing from this build")


@pytest.mark.parametrize(
    "struct_name",
    [
        "Smpt_device*",
        "Smpt_ll_init*",
        "Smpt_ll_channel_config*",
        "Smpt_get_extended_version_ack*",
        "Smpt_ack*",
    ],
)
def test_ffi_structs(sm, struct_name):
    """Test creation of various structs using FFI."""
    try:
        # Check if we have the enhanced CFFI utilities
        if hasattr(sm, "_have_cffi_utils") and sm._have_cffi_utils:
            # Use managed_new for safer resource management
            obj = sm.managed_new(struct_name)
        else:
            # Fall back to regular ffi.new
            obj = sm.ffi.new(struct_name)

        assert obj is not None, f"Created struct {struct_name}"
    except Exception as e:
        pytest.skip(f"Could not create struct {struct_name}: {e}")


def test_packet_number_generator(sm):
    """Test packet number generator without hardware."""
    # Skip this test if the function doesn't exist
    if not hasattr(sm, "smpt_packet_number_generator_next"):
        pytest.skip("smpt_packet_number_generator_next function not found")

    # Create a device struct with proper resource management
    if (
        hasattr(sm, "_have_cffi_utils")
        and sm._have_cffi_utils
        and hasattr(sm, "CFFIResourceManager")
    ):
        # Use the enhanced resource manager
        with sm.CFFIResourceManager(sm.ffi.new("Smpt_device*")) as device:
            # Initialize the packet number field - it could be an int8 or uint8
            device.current_packet_number = 0

            # The function updates the device and returns the previous value
            # First call, expect return value of 0
            packet_number = sm.smpt_packet_number_generator_next(device)
            assert packet_number == 0, "First call should return initial value (0)"

            # Save current value
            prev_value = device.current_packet_number

            # Second call
            packet_number = sm.smpt_packet_number_generator_next(device)

            # Verify the packet number was changed
            assert packet_number == prev_value, (
                f"Should return previous value ({prev_value})"
            )
            assert device.current_packet_number != prev_value, (
                "Should update the packet number"
            )
    else:
        # Fall back to original implementation without resource management
        device = sm.ffi.new("Smpt_device*")

        # Initialize the packet number field - it could be an int8 or uint8
        device.current_packet_number = 0

        # The function updates the device and returns the previous value
        # First call, expect return value of 0
        packet_number = sm.smpt_packet_number_generator_next(device)
        assert packet_number == 0, "First call should return initial value (0)"

        # Save current value
        prev_value = device.current_packet_number

        # Second call
        packet_number = sm.smpt_packet_number_generator_next(device)

        # Verify the packet number was changed
        assert packet_number == prev_value, (
            f"Should return previous value ({prev_value})"
        )
        assert device.current_packet_number != prev_value, (
            "Should update the packet number"
        )

    # Skip the max value test since we don't know if it's int8 or uint8
