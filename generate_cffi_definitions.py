#!/usr/bin/env python3
"""
CFFI Definition Generator for ScienceMode

This script generates static C definitions (sciencemode.cdef) by parsing
the ScienceMode C headers using pycparser. Run this script when the
C headers change to regenerate the definitions.

Requirements: pycparser, cffi

Usage: python generate_cffi_definitions.py
"""

import os
import sys

# Force UTF-8 encoding for all file operations - do this BEFORE any other imports
if sys.platform.startswith("win"):
    # On Windows, force UTF-8 encoding for all I/O operations
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"

import itertools
import platform
import re

import pycparser
from cffi import FFI
from pycparser import c_ast
from pycparser.c_generator import CGenerator

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir

# Print for debugging
print(f"Found ScienceMode in: {project_root}")

# Determine include and library paths - use current project structure
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

INCLUDE_PATTERN = re.compile(r"(-I)?(.*ScienceMode)")
DEFINE_PATTERN = re.compile(r"^#define\s+(\w+)\s+\(?([\w<|.\-+*/()\s]+)\)?", re.M)
DEFINE_BLACKLIST = {
    "main",
    # Header guard defines that should not be treated as constants
    "SMPT_API",
    "SMPT_CLIENT_CMD_LISTS_H",
    "SMPT_CLIENT_DATA_H",
    "SMPT_CLIENT_H",
    "SMPT_CLIENT_POWER_H",
    "SMPT_CLIENT_UTILS_H",
    "SMPT_DEFINITIONS_DATA_TYPES_H",
    "SMPT_DEFINITIONS_FILE_TRANSFER_H",
    "SMPT_DEFINITIONS_H",
    "SMPT_DEFINITIONS_INTERNAL_H",
    "SMPT_DEFINITIONS_POWER_H",
    "SMPT_DL_DEFINITIONS_DATA_TYPES_H",
    "SMPT_DL_DEFINITIONS_H",
    "SMPT_DL_PACKET_CLIENT_H",
    "SMPT_DL_PACKET_VALIDITY_H",
    "SMPT_DL_SERVER_H",
    "SMPT_FILE_H",
    "SMPT_LL_DEFINITIONS_DATA_TYPES_H",
    "SMPT_LL_DEFINITIONS_H",
    "SMPT_LL_MESSAGES_H",
    "SMPT_LL_PACKET_CLIENT_H",
    "SMPT_LL_PACKET_INTERNAL_H",
    "SMPT_LL_PACKET_VALIDITY_H",
    "SMPT_LL_SERIAL_PORT_LINUX_H",
    "SMPT_LL_SERIAL_PORT_WINDOWS_H",
    "SMPT_LL_SERVER_H",
    "SMPT_MESSAGES_H",
    "SMPT_ML_DEFINITIONS_DATA_TYPES_H",
    "SMPT_ML_DEFINITIONS_H",
    "SMPT_ML_PACKET_CLIENT_H",
    "SMPT_ML_PACKET_SERVER_H",
    "SMPT_ML_PACKET_UTILS_H",
    "SMPT_ML_PACKET_VALIDITY_H",
    "SMPT_PACKET_CLIENT_H",
    "SMPT_PACKET_GENERAL_H",
    "SMPT_PACKET_INPUT_BUFFER_DEFINITIONS_H",
    "SMPT_PACKET_INPUT_BUFFER_H",
    "SMPT_PACKET_INPUT_BUFFER_INTERNAL_H",
    "SMPT_PACKET_NUMBER_GENERATOR_H",
    "SMPT_PACKET_OUTPUT_BUFFER_H",
    "SMPT_PACKET_SERVER_H",
    "SMPT_PACKET_UTILS_H",
    "SMPT_PACKET_VALIDITY_H",
    "SMPT_SERIAL_PORT_H",
    # Problematic macro that causes overflow on some platforms
    "SMPT_DL_MAX_FILE_SIZE",
}

# Define GCC specific compiler extensions away - simplified + minimal bool
DEFINE_ARGS = [
    "-D__attribute__(x)=",
    "-D__inline=",
    "-D__restrict=",
    "-D__extension__=",
    "-D__GNUC_VA_LIST=",
    "-D__inline__=",
    "-D__forceinline=",
    "-D__volatile__=",
    "-D__MINGW_NOTHROW=",
    "-D__nothrow__=",
    "-DCRTIMP=",
    "-DSDL_FORCE_INLINE=",
    "-DDOXYGEN_SHOULD_IGNORE_THIS=",
    "-D_PROCESS_H_=",
    "-U__GNUC__",
    "-Ui386",
    "-U__i386__",
    "-U__MINGW32__",
    "-DNT_INCLUDED",
    # Minimal bool support - just enough for pycparser to understand modern headers
    "-D_Bool=_Bool",
    "-Dbool=_Bool",
    "-Dtrue=1",
    "-Dfalse=0",
    # Windows types that pycparser needs to understand
    "-DHANDLE=void*",
    # Fix problematic macro that causes overflow - provide safe fallback
    "-DSMPT_DL_MAX_FILE_SIZE=2147483647",
    "-L" + smpt_lib_path,
    "-Iutils/fake_libc_include",
    "-Iutils/fake_windows_include",
    "-I" + smpt_include_path1,
    "-I" + smpt_include_path2,
    "-I" + smpt_include_path3,
    "-I" + smpt_include_path4,
]

# Add platform-specific defines
if platform.system() == "Windows":
    DEFINE_ARGS.extend(["-D_WIN32", "-D_MSC_VER=1900"])
elif platform.system() == "Linux":
    DEFINE_ARGS.append("-D__linux__")
elif platform.system() == "Darwin":
    DEFINE_ARGS.extend(
        [
            "-D__APPLE__",
            "-D__MACH__",
            # Ensure macOS doesn't trigger MSVC-specific code paths
            "-U_MSC_VER",
            "-U_WIN32",
            "-UWIN32",
            # Define away problematic Apple-specific macros that confuse pycparser
            "-D__builtin_available(...)=1",
            "-D__has_feature(x)=0",
            "-D__has_extension(x)=0",
            "-D__has_attribute(x)=0",
        ]
    )

FUNCTION_BLACKLIST = {
    # Functions that are declared in headers but missing implementations on some
    # platforms (macOS)
    "smpt_get_dl_get_ack",
    "smpt_get_dl_init_ack",
    "smpt_get_dl_power_module_ack",
    "smpt_get_dl_send_file",
    "smpt_get_dl_send_live_data",
    "smpt_get_dl_send_mmi",
    "smpt_get_dl_stop_ack",
    "smpt_get_dl_sys_ack",
    "smpt_is_valid_dl_get",
    "smpt_is_valid_dl_get_ack",
    # Additional missing dyscom-level validation functions found in macOS build failures
    "smpt_is_valid_dl_init",
    "smpt_is_valid_dl_init_ack",
    "smpt_is_valid_dl_power_module",
    "smpt_is_valid_dl_power_module_ack",
    "smpt_is_valid_dl_send_file",
    "smpt_is_valid_dl_send_live_data",
    "smpt_is_valid_dl_send_mmi",
    "smpt_is_valid_dl_start_ack",
    "smpt_is_valid_dl_stop_ack",
    "smpt_is_valid_dl_sys",
    "smpt_is_valid_dl_sys_ack",
    # Missing dyscom-level send functions on macOS (found in compilation failures)
    "smpt_send_dl_get",
    "smpt_send_dl_init",
    "smpt_send_dl_power_module",
    "smpt_send_dl_send_file_ack",
    "smpt_send_dl_start",
    "smpt_send_dl_stop",
    "smpt_send_dl_sys",
}

VARIADIC_ARG_PATTERN = re.compile(r"va_list \w+")
ARRAY_SIZEOF_PATTERN = re.compile(r"\[[^\]]*sizeof[^\]]*]")

HEADERS = [
    "general/smpt_client_data.h",
    "general/smpt_definitions_data_types.h",
    "general/smpt_client_cmd_lists.h",
    "general/smpt_definitions.h",
    "general/smpt_definitions_internal.h",
    "general/smpt_messages.h",
    "general/packet/smpt_packet_general.h",
    "general/packet/smpt_packet_internal.h",
    "general/packet/smpt_packet_validity.h",
    "general/packet/smpt_packet_utils.h",
    "general/packet/smpt_packet_client.h",
    "general/packet/smpt_packet_server.h",
    "general/packet_input_buffer/smpt_packet_input_buffer.h",
    "general/packet_input_buffer/smpt_packet_input_buffer_definitions.h",
    "general/packet_input_buffer/smpt_packet_input_buffer_internal.h",
    "general/packet_output_buffer/smpt_packet_output_buffer.h",
    "general/serial_port/smpt_serial_port.h",
    "general/serial_port/smpt_serial_port_windows.h",
    "general/serial_port/smpt_serial_port_linux.h",
    "general/smpt_definitions_file_transfer.h",
    "general/smpt_file.h",
    "general/smpt_packet_number_generator.h",
    "general/smpt_definitions_power.h",
    "general/smpt_client_power.h",
    "general/smpt_client_utils.h",
    "low-level/smpt_ll_definitions.h",
    "low-level/smpt_ll_packet_client.h",
    "low-level/smpt_ll_packet_server.h",
    "low-level/smpt_ll_packet_validity.h",
    "low-level/smpt_ll_definitions_data_types.h",
    "low-level/smpt_ll_messages.h",
    "mid-level/smpt_ml_definitions.h",
    "mid-level/smpt_ml_packet_client.h",
    "mid-level/smpt_ml_packet_server.h",
    "mid-level/smpt_ml_packet_validity.h",
    "mid-level/smpt_ml_packet_utils.h",
    "mid-level/smpt_ml_definitions_data_types.h",
    "dyscom-level/smpt_dl_definitions.h",
    "dyscom-level/smpt_dl_packet_client.h",
    "dyscom-level/smpt_dl_packet_server.h",
    "dyscom-level/smpt_dl_packet_validity.h",
    "dyscom-level/smpt_dl_packet_utils.h",
    "dyscom-level/smpt_dl_definitions_data_types.h",
]

ROOT_HEADERS = [
    "general/smpt_client.h",
    "dyscom-level/smpt_dl_client.h",
    "low-level/smpt_ll_client.h",
    "mid-level/smpt_ml_client.h",
]


class Collector(c_ast.NodeVisitor):
    def __init__(self):
        self.generator = CGenerator()
        self.typedecls = []
        self.functions = []

    def process_typedecl(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            typedecl = f"{self.generator.visit(node)};"
            typedecl = ARRAY_SIZEOF_PATTERN.sub("[...]", typedecl)
            if typedecl not in self.typedecls:
                self.typedecls.append(typedecl)

    def sanitize_enum(self, enum):
        for _name, enumeratorlist in enum.children():
            for _name, enumerator in enumeratorlist.children():
                enumerator.value = c_ast.Constant("dummy", "...")
        return enum

    def visit_Typedef(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            if isinstance(node.type, c_ast.TypeDecl) and isinstance(
                node.type.type, c_ast.Enum
            ):
                self.sanitize_enum(node.type.type)
            self.process_typedecl(node)

    def visit_Union(self, node):
        self.process_typedecl(node)

    def visit_Struct(self, node):
        self.process_typedecl(node)

    def visit_Enum(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            node = self.sanitize_enum(node)
            self.process_typedecl(node)

    def visit_FuncDecl(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            if isinstance(node.type, c_ast.PtrDecl):
                function_name = node.type.type.declname
            else:
                function_name = node.type.declname
            if function_name in FUNCTION_BLACKLIST:
                return
            decl = f"{self.generator.visit(node)};"
            decl = VARIADIC_ARG_PATTERN.sub("...", decl)
            if decl not in self.functions:
                self.functions.append(decl)


ffi = FFI()

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


def find_cpp_executable():
    """Find available C preprocessor executable, prioritizing MSVC on Windows."""
    import glob
    import shutil

    if sys.platform.startswith("win"):
        # First try to find cl.exe from Visual Studio installations
        vs_paths = [
            "C:/Program Files/Microsoft Visual Studio/*/Enterprise/VC/Tools/"
            "MSVC/*/bin/Hostx64/x64/cl.exe",
            "C:/Program Files/Microsoft Visual Studio/*/Professional/VC/Tools/"
            "MSVC/*/bin/Hostx64/x64/cl.exe",
            "C:/Program Files/Microsoft Visual Studio/*/Community/VC/Tools/"
            "MSVC/*/bin/Hostx64/x64/cl.exe",
            "C:/Program Files (x86)/Microsoft Visual Studio/*/Enterprise/"
            "VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "C:/Program Files (x86)/Microsoft Visual Studio/*/Professional/"
            "VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "C:/Program Files (x86)/Microsoft Visual Studio/*/Community/"
            "VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
        ]

        for pattern in vs_paths:
            matches = glob.glob(pattern)
            if matches:
                # Use the first (usually latest) version found
                cl_path = matches[0]
                print(f"Found MSVC compiler: {cl_path}")
                return cl_path, "cl"

        # Fallback to other compilers
        candidates = [
            ("cl.exe", "cl"),
            ("cpp.exe", "cpp"),
            ("gcc.exe", "gcc"),
            ("clang.exe", "clang"),
        ]
    else:
        candidates = [("cpp", "cpp"), ("gcc", "gcc"), ("clang", "clang")]

    for candidate, compiler_type in candidates:
        cpp_path = shutil.which(candidate)
        if cpp_path:
            print(f"Found C preprocessor: {cpp_path}")
            return cpp_path, compiler_type

    return None, None


# Try to find C preprocessor
cpp_path, compiler_type = find_cpp_executable()

if not cpp_path:
    raise RuntimeError(
        "No C preprocessor found. Please install Visual Studio, GCC, or Clang."
    )

if compiler_type == "cl":
    # MSVC cl.exe needs special arguments for preprocessing
    msvc_args = []
    for arg in DEFINE_ARGS:
        if arg.startswith("-D"):
            msvc_args.append("/D" + arg[2:])
        elif arg.startswith("-I"):
            msvc_args.append("/I" + arg[2:])
        elif not arg.startswith("-L") and not arg.startswith("-U"):
            # Skip linker and undefine args for preprocessing
            continue

    pycparser_args = {
        "use_cpp": True,
        "cpp_path": cpp_path,
        "cpp_args": ["/EP"] + msvc_args,  # /EP = preprocess only
    }
    print("Using MSVC cl.exe for preprocessing")
else:
    # Standard GCC/Clang-style preprocessor
    pycparser_args = {
        "use_cpp": True,
        "cpp_args": DEFINE_ARGS,
        "cpp_path": cpp_path,
    }
    print(f"Using {compiler_type} for preprocessing")

print("Starting CFFI parsing with simplified approach...")

collector = Collector()
for header in ROOT_HEADERS:
    print(f"Parsing {header}...")
    header_path = os.sep.join([include_dir, header])

    try:
        ast = pycparser.parse_file(header_path, **pycparser_args)
        collector.visit(ast)
        print(f"Successfully parsed {header}")

    except Exception as e:
        print(f"Failed to parse {header}: {e}")

        # macOS-specific fallback: try with minimal preprocessor args
        if platform.system() == "Darwin":
            print(f"Attempting macOS fallback parsing for {header}...")

            # Minimal args that work better with pycparser on macOS
            fallback_args = {
                "use_cpp": True,
                "cpp_path": cpp_path,
                "cpp_args": [
                    "-I" + smpt_include_path1,
                    "-I" + smpt_include_path2,
                    "-I" + smpt_include_path3,
                    "-I" + smpt_include_path4,
                    "-Iutils/fake_libc_include",
                    "-D__attribute__(x)=",
                    "-D__inline=",
                    "-D__APPLE__",
                    "-D__MACH__",
                    "-U_MSC_VER",
                    "-U_WIN32",
                ],
            }

            try:
                ast = pycparser.parse_file(header_path, **fallback_args)
                collector.visit(ast)
                print(f"Successfully parsed {header} with macOS fallback")
                continue
            except Exception as fallback_error:
                print(f"macOS fallback also failed: {fallback_error}")

        raise RuntimeError(
            f"Header parsing failed for {header}. "
            "Cannot proceed without C preprocessor."
        ) from e

defines = set()
for header_path in HEADERS:
    with open(os.sep.join([include_dir, header_path]), encoding="utf-8") as header_file:
        header = header_file.read()
        for match in DEFINE_PATTERN.finditer(header):
            if (
                match.group(1) in DEFINE_BLACKLIST
                or match.group(1) in collector.typedecls
                or match.group(1) in collector.functions
            ):
                continue
            try:
                int(match.group(2), 0)
                defines.add(f"#define {match.group(1)} {match.group(2)}")
            except ValueError:
                defines.add(f"#define {match.group(1)} ...")

# Add safe fallback for problematic constants that might be missing or cause overflow
safe_fallbacks = {
    # Commenting out SMPT_DL_MAX_FILE_SIZE - let it be excluded entirely to avoid
    # CFFI issues
    # "SMPT_DL_MAX_FILE_SIZE": "2147483647",  # Max 32-bit signed int to avoid
    # overflow issues
}

existing_defines = {line.split()[1] for line in defines if line.startswith("#define ")}

for const_name, const_value in safe_fallbacks.items():
    if const_name not in existing_defines:
        print(f"Adding safe fallback: {const_name} = {const_value}")
        defines.add(f"#define {const_name} {const_value}")
    else:
        # Replace problematic "..." definitions with safe values
        defines = {
            line
            if not line.startswith(f"#define {const_name} ...")
            else f"#define {const_name} {const_value}"
            for line in defines
        }
        print(f"Replaced problematic definition: {const_name} = {const_value}")

# macOS fallback: manually add critical missing constants if not found
if platform.system() == "Darwin":
    critical_constants = {
        "SMPT_DL_1KHZ": "1000",
        "SMPT_DL_2KHZ": "2000",
        "SMPT_DL_4KHZ": "4000",
        "SMPT_DL_FILE_SIZE_BYTES": "8",
        "SMPT_DL_GUID_STRING_LENGTH": "36",
        "SMPT_DL_MAX_BLOCK_BYTES_LENGTH": "512",
        "SMPT_DL_MAX_CHANNELS": "8",
        "SMPT_DL_MAX_FILE_ID_LENGTH": "60",
        "SMPT_DL_MAX_STRING_LENGTH": "128",
        # Excluded problematic macro - causes overflow issues on some compilers
        # "SMPT_DL_MAX_FILE_SIZE": "2147483647",
    }

    existing_defines = {
        line.split()[1] for line in defines if line.startswith("#define ")
    }

    for const_name, const_value in critical_constants.items():
        if const_name not in existing_defines:
            print(
                f"macOS fallback: Adding missing constant {const_name} = {const_value}"
            )
            defines.add(f"#define {const_name} {const_value}")
        else:
            print(f"macOS: Found {const_name} in extracted defines")

print(
    f"Processing {len(defines)} defines, {len(collector.typedecls)} types, "
    f"{len(collector.functions)} functions"
)

cdef = "\n".join(itertools.chain(*[defines, collector.typedecls, collector.functions]))

# Simple, reliable string replacements from original
cdef = cdef.replace("[Smpt_Length_Max_Packet_Size]", "[1200]")
cdef = cdef.replace("[Smpt_Length_Packet_Input_Buffer_Rows]", "[100]")
cdef = cdef.replace(
    "[Smpt_Length_Packet_Input_Buffer_Rows * Smpt_Length_Max_Packet_Size]", "[120000]"
)
cdef = cdef.replace("[Smpt_Length_Serial_Port_Chars]", "[256]")
cdef = cdef.replace("[Smpt_Length_Number_Of_Acks]", "[100]")
cdef = cdef.replace("[Smpt_Length_Device_Id]", "[10]")
cdef = cdef.replace("[Smpt_Length_Points]", "[16]")
cdef = cdef.replace("[Smpt_Length_Number_Of_Channels]", "[8]")

# Fix _Bool array compatibility issues by converting to unsigned char arrays
# This matches what the headers use and prevents CFFI type conflicts
cdef = re.sub(r"\b_Bool\s*\[([^\]]*)\]", r"unsigned char[\1]", cdef)
cdef = re.sub(r"\bbool\s*\[([^\]]*)\]", r"unsigned char[\1]", cdef)


# Fix platform-specific struct fields - create a platform-appropriate struct
# The Smpt_device struct has different fields on different platforms due to
# #ifdef blocks
def fix_platform_specific_structs(cdef_content):
    """Fix structs that have platform-specific fields by creating
    platform-appropriate definitions."""

    # Pattern to match any Smpt_device struct definition
    device_struct_pattern = (
        r"typedef struct[^{]*\{[^}]*serial_port[^}]*\}[^;]*Smpt_device;"
    )

    # Check if we have any Smpt_device struct definition
    if re.search(device_struct_pattern, cdef_content, re.DOTALL):
        print(
            f"Found Smpt_device struct, creating {platform.system()}-specific "
            "version..."
        )

        if platform.system() == "Windows":
            # Windows version with HANDLE - use flexible struct to avoid size issues
            platform_struct = """typedef struct
{
  uint32_t packet_length;
  char packet[1200];
  Smpt_cmd_list cmd_list;
  void* serial_port_handle_;
  char current_packet_number;
  char serial_port_name[256];
  Packet_input_buffer packet_input_buffer;
  uint8_t packet_input_buffer_data[120000];
  uint8_t packet_input_buffer_state[100];
} Smpt_device;"""
        else:
            # Linux/macOS version with descriptor - include
            # packet field for size consistency
            platform_struct = """typedef struct
{
  uint32_t packet_length;
  uint8_t packet[1200];
  Smpt_cmd_list cmd_list;
  int serial_port_descriptor;
  int8_t current_packet_number;
  char serial_port_name[256];
  Packet_input_buffer packet_input_buffer;
  uint8_t packet_input_buffer_data[120000];
  uint8_t packet_input_buffer_state[100];
} Smpt_device;"""

        # Replace any existing Smpt_device struct with the platform-appropriate one
        cdef_content = re.sub(
            device_struct_pattern, platform_struct, cdef_content, flags=re.DOTALL
        )
        print(
            f"Replaced Smpt_device with {platform.system()}-specific definition "
            "(Windows uses flexible struct, Linux uses explicit packet field)"
        )

    return cdef_content


cdef = fix_platform_specific_structs(cdef)

ffi.cdef(cdef)

print("CFFI configuration completed successfully!")

# Save generated definitions to file
cdef_output_path = os.path.join(current_dir, "sciencemode", "sciencemode.cdef")
with open(cdef_output_path, "w", encoding="utf-8") as file:
    file.write(cdef)
print(f"Generated CFFI definitions saved to: {cdef_output_path}")
