#!/usr/bin/env python

"""
Testing utilities for ScienceMode4 Python Wrapper.
Provides mock implementations of functions for testing without hardware.
"""

import platform

import pytest


class SMPTMock:
    """Mock implementation of SMPT functions for testing."""

    @staticmethod
    def smpt_packet_number_generator_next(device):
        """Mock implementation of packet number generator."""
        # Increment packet number and handle rollover
        if device.current_packet_number >= 255:
            device.current_packet_number = 1
        else:
            device.current_packet_number += 1
        return device.current_packet_number

    @staticmethod
    def smpt_check_serial_port(port_name):
        """Mock implementation of serial port check."""
        # Always return success for testing
        return 0  # Smpt_Status_Ok

    @staticmethod
    def smpt_open_serial_port(device, port_name):
        """Mock implementation of open serial port."""
        # Copy port name to device
        port_str = ""
        if isinstance(port_name, bytes):
            port_str = port_name.decode("utf-8")
        else:
            try:
                # Extract string from FFI char array
                from sciencemode import sciencemode as sm

                port_str = sm.ffi.string(port_name).decode("utf-8")
            except Exception:
                port_str = "COM1" if platform.system() == "Windows" else "/dev/ttyUSB0"

        # Set the port name in the device
        try:
            from sciencemode import sciencemode as sm

            max_len = getattr(sm, "Smpt_Length_Serial_Port_Chars", 256) - 1
            for i in range(min(len(port_str), max_len)):
                device.serial_port_name[i] = ord(port_str[i])
            device.serial_port_name[min(len(port_str), max_len)] = 0  # Null terminator
        except Exception:
            pass

        # Set initial packet number
        device.current_packet_number = 0

        return 0  # Smpt_Status_Ok

    @staticmethod
    def smpt_close_serial_port(device):
        """Mock implementation of close serial port."""
        return 0  # Smpt_Status_Ok

    @staticmethod
    def smpt_new_packet_received(device):
        """Mock implementation to check if a new packet was received."""
        # For testing, randomly return True or False
        import random

        return random.choice([True, False])


# Pytest fixture to inject mock functions
@pytest.fixture(scope="session", autouse=True)
def inject_mocks():
    """
    Pytest fixture that injects mock functions into sciencemode module.
    This runs automatically before any tests.
    """
    try:
        # sciencemode import moved to next line
        from sciencemode import sciencemode as sm_module

        # Only inject if the real functions are not already available
        mock = SMPTMock()

        # Create a list of function names and their implementations
        functions_to_inject = [
            (
                "smpt_packet_number_generator_next",
                mock.smpt_packet_number_generator_next,
            ),
            ("smpt_check_serial_port", mock.smpt_check_serial_port),
            ("smpt_open_serial_port", mock.smpt_open_serial_port),
            ("smpt_close_serial_port", mock.smpt_close_serial_port),
            ("smpt_new_packet_received", mock.smpt_new_packet_received),
        ]

        # Inject each function if not already present
        injected = []
        for func_name, func_impl in functions_to_inject:
            if not hasattr(sm_module, func_name):
                setattr(sm_module, func_name, func_impl)
                injected.append(func_name)

        if injected:
            print(f"Injected mock functions: {', '.join(injected)}")

        return True
    except ImportError as e:
        print(f"Error injecting mock functions: {e}")
        return False


# Function to manually inject mocks (for direct script execution)
def inject_mock_functions():
    """Manually inject mock functions into sciencemode module."""
    try:
        # sciencemode import moved to next line
        from sciencemode import sciencemode as sm_module

        # Only inject if the real functions are not already available
        mock = SMPTMock()

        # Create a list of function names and their implementations
        functions_to_inject = [
            (
                "smpt_packet_number_generator_next",
                mock.smpt_packet_number_generator_next,
            ),
            ("smpt_check_serial_port", mock.smpt_check_serial_port),
            ("smpt_open_serial_port", mock.smpt_open_serial_port),
            ("smpt_close_serial_port", mock.smpt_close_serial_port),
            ("smpt_new_packet_received", mock.smpt_new_packet_received),
        ]

        # Inject each function if not already present
        injected = []
        for func_name, func_impl in functions_to_inject:
            if not hasattr(sm_module, func_name):
                setattr(sm_module, func_name, func_impl)
                injected.append(func_name)

        if injected:
            print(f"Injected mock functions: {', '.join(injected)}")

        return True
    except ImportError as e:
        print(f"Error injecting mock functions: {e}")
        return False
