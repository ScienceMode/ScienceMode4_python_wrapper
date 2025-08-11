import os
import sys

# Force UTF-8 encoding for all file operations - do this BEFORE any other imports
if sys.platform.startswith("win"):
    # On Windows, force UTF-8 encoding for all I/O operations
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"

from cffi import FFI

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Print for debugging
print(f"Found ScienceMode in: {project_root}")

# Determine include and library paths
smpt_submodule_path = os.path.join(project_root, "sciencemode")
if os.path.exists(smpt_submodule_path):
    devel_root = smpt_submodule_path
    print(f"Using submodule SMPT library: {devel_root}")
else:
    # Try current directory structure
    devel_root = os.path.join(project_root, "smpt", "ScienceMode_Library")
    print(f"Using local SMPT library: {devel_root}")

include_dir = os.path.join(devel_root, "include")

# Check if we have the include directory
if not os.path.exists(include_dir):
    raise FileNotFoundError(f"SMPT include directory not found at: {include_dir}")

smpt_lib_path = os.path.join(project_root, "lib")

smpt_include_path1 = os.path.join(include_dir, "general")
smpt_include_path2 = os.path.join(include_dir, "low-level")
smpt_include_path3 = os.path.join(include_dir, "mid-level")
smpt_include_path4 = os.path.join(include_dir, "dyscom-level")

# Root headers to include in the set_source
ROOT_HEADERS = [
    "general/smpt_client.h",
    "dyscom-level/smpt_dl_client.h",
    "low-level/smpt_ll_client.h",
    "mid-level/smpt_ml_client.h",
]

# Initialize FFI
ffi = FFI()

# Load pre-generated C definitions
cdef_file = os.path.join(current_dir, "sciencemode.cdef")
if not os.path.exists(cdef_file):
    raise FileNotFoundError(
        f"Pre-generated CFFI definitions not found at: {cdef_file}\n"
        f"Please run the definition generator script to create this file."
    )

print(f"Loading pre-generated CFFI definitions from: {cdef_file}")
with open(cdef_file, encoding="utf-8") as f:
    cdef_content = f.read()

# Apply the C definitions to FFI
ffi.cdef(cdef_content)

# Set the source configuration for compilation
ffi.set_source(
    "sciencemode._sciencemode",
    ("\n").join(f'#include "{header}"' for header in ROOT_HEADERS)
    + '\n#include "dyscom-level/smpt_dl_definitions_data_types.h"',
    include_dirs=[
        include_dir,
        smpt_include_path1,
        smpt_include_path2,
        smpt_include_path3,
        smpt_include_path4,
    ],
    libraries=["smpt"],
    library_dirs=["./lib"],
)

print("CFFI configuration completed successfully!")
