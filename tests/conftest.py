#!/usr/bin/env python

"""
Pytest configuration for ScienceMode tests.
"""

import os
import sys

# Add parent directory to path to allow importing from parent
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def pytest_configure(config):
    """Configure pytest."""
    # Import and inject mock functions at the start of the test session
    try:
        import importlib.util

        # Get the path to test_utils.py
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        test_utils_path = os.path.join(tests_dir, "test_utils.py")

        # Import test_utils.py using importlib
        if os.path.exists(test_utils_path):
            # Load the module
            spec = importlib.util.spec_from_file_location("test_utils", test_utils_path)
            test_utils = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_utils)

            # Call the function
            if test_utils.inject_mock_functions():
                print("Successfully injected mock functions for testing")
        else:
            print(f"Warning: Could not find {test_utils_path}")
    except Exception as e:
        print(f"Warning: Could not inject mock functions: {e}")


def pytest_report_header(config):
    """Add information to the pytest header."""
    import platform

    return [
        "Testing ScienceMode CFFI wrapper",
        f"Platform: {platform.platform()}",
        f"Python: {platform.python_version()}",
    ]
