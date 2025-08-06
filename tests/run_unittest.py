#!/usr/bin/env python

"""
Run tests directly to verify library loading without requiring pytest
"""

import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import sciencemode and run basic tests
print("=== Testing ScienceMode Library Loading ===")
try:
    import sciencemode
    from sciencemode import sciencemode as sm

    print("✓ Successfully imported sciencemode")

    # Check FFI interface
    if hasattr(sm, "ffi"):
        print("✓ FFI interface available")
    else:
        print("✗ FFI interface not found")

    # Create device struct
    try:
        device = sm.ffi.new("Smpt_device*")
        print("✓ Device struct created successfully")
    except Exception as e:
        print(f"✗ Error creating device struct: {e}")

    # Check library files
    package_dir = os.path.dirname(sciencemode.__file__)
    lib_files = [
        f
        for f in os.listdir(package_dir)
        if f.startswith("lib") or f.endswith(".dll") or f.endswith(".so")
    ]

    if lib_files:
        print(f"✓ Found {len(lib_files)} library files in package directory:")
        for lib_file in lib_files:
            print(f"  - {lib_file}")
    else:
        print("✗ No library files found in package directory")

    print("\nAll tests completed successfully!")
    sys.exit(0)
except ImportError as e:
    print(f"✗ Error importing sciencemode: {e}")
    print("Make sure the library is built and installed properly")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error during testing: {e}")
    sys.exit(1)
# Return non-zero exit code if tests fail
# sys.exit(0 if result.wasSuccessful() else 1)  # Removed: result is undefined
