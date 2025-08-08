"""
CFFI wrapper for ScienceMode library.

This module uses CFFI to provide Python bindings for the ScienceMode library.
It handles the compilation, linking, and loading of the C library, and provides
utility functions for working with the CFFI interface.

The module offers:
- Automatic header file and library detection
- Platform-specific handling for Windows, macOS, and Linux
- Resource management through context managers
- Memory management helpers
- Error handling utilities
- String conversion functions
"""

import glob
import itertools
import os
import platform
import re
import sys

import pycparser
from cffi import FFI
from pycparser import c_ast
from pycparser.c_generator import CGenerator

# Regular expressions for parsing include paths and #define statements
INCLUDE_PATTERN = re.compile(r"(-I)?(.*ScienceMode)")
DEFINE_PATTERN = re.compile(r"^#define\s+(\w+)\s+\(?([\w<|.]+)\)?", re.M)

# List of symbols that should not be processed as #define statements
DEFINE_BLACKLIST = {
    "main",
}

# Get the directory where this _cffi.py file is located (package directory)
package_dir = os.path.dirname(os.path.abspath(__file__))

# Try to find the include directory in different locations
# Check installed package directory first, then development locations
devel_root_candidates = [
    os.path.join(package_dir, "include"),  # Bundled in package directory (installed)
    os.path.abspath(
        "./smpt/ScienceMode_Library/include"
    ),  # Standard source tree layout
    os.path.abspath("./smpt/ScienceMode_Library"),  # Alternative source layout
    os.path.abspath("../smpt/ScienceMode_Library/include"),  # When in a subdirectory
    os.path.abspath("../smpt/ScienceMode_Library"),  # When in a subdirectory
    os.path.abspath("../include/ScienceMode4"),  # Installed version layout
    os.path.abspath("./include/ScienceMode4"),  # Installed version layout
]

# Find the first valid include directory
include_dir = None
for candidate in devel_root_candidates:
    if os.path.exists(os.path.join(candidate, "general")) or os.path.exists(candidate):
        include_dir = candidate
        break

# If none found, default to the first one (will fail but with clear error)
if include_dir is None:
    include_dir = os.path.join(devel_root_candidates[0], "include")
    print(
        f"Warning: Could not find ScienceMode include directory. "
        f"Using default: {include_dir}"
    )
else:
    print(f"Found ScienceMode include directory: {include_dir}")

# Define library path and check if it exists
# First check package directory (installed), then development directory
package_dir = os.path.dirname(os.path.abspath(__file__))
smpt_lib_paths = [
    package_dir,  # Bundled in package directory (installed)
    os.path.abspath("./lib"),  # Development directory
]

# Find the first directory that contains library files
smpt_lib_path = os.path.abspath("./lib")  # Default fallback
lib_found = False

if platform.system() == "Windows":
    # Prefer static libraries (.lib) for wheel distribution
    lib_patterns = ["smpt.lib", "libsmpt.lib", "smpt.dll", "libsmpt.dll"]
elif platform.system() == "Darwin":
    # Prefer static libraries (.a) for wheel distribution
    lib_patterns = ["libsmpt.a", "libsmpt.dylib"]
else:
    # Prefer static libraries (.a) for wheel distribution
    lib_patterns = ["libsmpt.a", "libsmpt.so"]

# Check each possible library path
for lib_path in smpt_lib_paths:
    for pattern in lib_patterns:
        if glob.glob(os.path.join(lib_path, pattern)):
            smpt_lib_path = lib_path
            lib_found = True
            break
    if lib_found:
        break

# If no library found, fall back to creating ./lib directory (development mode)
if not lib_found:
    # Create lib directory if it doesn't exist
    if not os.path.exists(smpt_lib_path):
        try:
            print(f"Creating lib directory: {smpt_lib_path}")
            os.makedirs(smpt_lib_path, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create lib directory: {e}")

    # Check for SMPT library existence in the created directory
    for pattern in lib_patterns:
        if glob.glob(os.path.join(smpt_lib_path, pattern)):
            lib_found = True
            break

if not lib_found:
    print("*" * 80)
    print(f"Warning: No SMPT library found in {smpt_lib_path}")
    print("Ensure that 'pip install -e .' completed successfully.")
    print("The setup.py script should build the SMPT library using CMake.")
    print("*" * 80)
else:
    print(f"Found SMPT library in: {smpt_lib_path}")

# Set the include paths based on the directory structure
if os.path.exists(os.path.join(include_dir, "general")):
    # Standard structure from source tree
    smpt_include_path1 = os.path.join(include_dir, "general")
    smpt_include_path2 = os.path.join(include_dir, "low-level")
    smpt_include_path3 = os.path.join(include_dir, "mid-level")
    smpt_include_path4 = os.path.join(include_dir, "dyscom-level")
else:
    # In the installed version, all files are in the same directory
    smpt_include_path1 = include_dir
    smpt_include_path2 = include_dir
    smpt_include_path3 = include_dir
    smpt_include_path4 = include_dir

# define GCC specific compiler extensions away
# Define preprocessor arguments for pycparser
# These definitions help parse the header files correctly by:
# 1. Setting the appropriate platform macros based on the current system
# 2. Defining away GCC-specific extensions that pycparser can't handle
# 3. Setting up include paths for both real headers and fake headers
DEFINE_ARGS = [
    # Platform definitions - set according to current platform
    # but make sure to handle platform-specific fields in structures
    "-D{}".format(
        "_WIN32"
        if sys.platform.startswith("win")
        else "__APPLE__"
        if sys.platform.startswith("darwin")
        else "__linux__"
    ),
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
    "-D_MSC_VER=1900",
    # Define HANDLE type for Windows to make CFFI happy
    "-DHANDLE=void*",
    "-L" + smpt_lib_path,
    "-Iutils/fake_libc_include",
    "-Iutils/fake_windows_include",
    "-I" + smpt_include_path1,
    "-I" + smpt_include_path2,
    "-I" + smpt_include_path3,
    "-I" + smpt_include_path4,
]

# List of function names that should be excluded from processing
FUNCTION_BLACKLIST = {}  # Empty for now, but can be populated if needed

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

# Headers to include
if os.path.exists(os.path.join(include_dir, "general")):
    # Standard structure from source tree
    ROOT_HEADERS = [
        "general/smpt_client.h",
        "dyscom-level/smpt_dl_client.h",
        "low-level/smpt_ll_client.h",
        "mid-level/smpt_ml_client.h",
    ]
else:
    # In the installed version, all files are in the same directory
    ROOT_HEADERS = [
        "smpt_client.h",
        "smpt_dl_client.h",
        "smpt_ll_client.h",
        "smpt_ml_client.h",
    ]


class Collector(c_ast.NodeVisitor):
    """AST visitor that collects type declarations and function definitions.

    This class walks through the Abstract Syntax Tree (AST) of C code and
    extracts all type declarations (structs, enums, typedefs) and function
    declarations for use with CFFI.
    """

    def __init__(self):
        """Initialize the collector with empty lists for types and functions."""
        self.generator = CGenerator()  # For generating C code from AST nodes
        self.typedecls = []  # Will hold all type declarations
        self.functions = []  # Will hold all function declarations

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


# Function to initialize the library once
def _init_smpt_lib():
    """Initialize the ScienceMode library once during the program's lifetime."""
    print("Initializing ScienceMode library...")
    # Any one-time initialization could go here
    return {
        "include_dir": include_dir,
        "lib_path": smpt_lib_path,
        "platform": platform.system(),
    }


# Function to load library directly (useful for testing and debug)
def load_library():  # noqa: C901
    """Try to load the SMPT library directly using ffi.dlopen().

    This is useful for direct testing without building the extension module.
    Returns the loaded library or None if not found.
    """
    # Choose library pattern based on platform
    if platform.system() == "Windows":
        patterns = ["smpt.dll", "libsmpt.dll"]
    elif platform.system() == "Darwin":
        patterns = ["libsmpt.dylib"]
    else:
        patterns = ["libsmpt.so"]

    # Try to load the library from the lib path
    for pattern in patterns:
        try:
            lib_path = os.path.join(smpt_lib_path, pattern)
            if os.path.exists(lib_path):
                print(f"Loading library from: {lib_path}")
                return ffi.dlopen(lib_path)
        except Exception as e:
            print(f"Failed to load {pattern}: {e}")
            if platform.system() == "Windows":
                try:
                    # Use ctypes for Windows error handling
                    import ctypes

                    # Check if we're on Windows to safely use windll
                    if sys.platform.startswith("win"):
                        try:
                            # Try to get Windows error details
                            windll_attr = getattr(ctypes, "windll", None)
                            if windll_attr:
                                kernel32 = getattr(windll_attr, "kernel32", None)
                                if kernel32:
                                    get_error = getattr(kernel32, "GetLastError", None)
                                    if get_error:
                                        error_code = get_error()
                                        print(f"Windows error code: {error_code}")

                                        # Try to format the error message
                                        try:
                                            FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
                                            FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

                                            # Buffer for the error message
                                            buffer_size = 256
                                            buffer = ctypes.create_string_buffer(
                                                buffer_size
                                            )

                                            # Get the error message
                                            format_msg = getattr(
                                                kernel32, "FormatMessageA", None
                                            )
                                            if format_msg:
                                                format_msg(
                                                    FORMAT_MESSAGE_FROM_SYSTEM
                                                    | FORMAT_MESSAGE_IGNORE_INSERTS,
                                                    None,
                                                    error_code,
                                                    0,
                                                    buffer,
                                                    buffer_size,
                                                    None,
                                                )

                                                # Convert message to Python string
                                                message = buffer.value.decode(
                                                    "utf-8", errors="replace"
                                                ).strip()
                                                print(f"Windows error: {message}")
                                        except Exception as msg_err:
                                            print(f"Error formatting: {msg_err}")
                                    else:
                                        print("GetLastError not available")
                                else:
                                    print("kernel32 not available")
                            else:
                                print("windll not available")
                        except Exception:
                            print("Error accessing Windows functionality")
                    else:
                        print("Not on Windows, skipping error handling")
                except Exception as win_err:
                    print(f"Error getting Windows error details: {win_err}")
            else:
                try:
                    if hasattr(ffi, "errno"):
                        print(f"Error code: {ffi.errno}")
                    else:
                        print("Error occurred but errno not available")
                except Exception as err_ex:
                    print(f"Error getting error code: {err_ex}")

    print("Could not load library directly")
    return None


# Determine appropriate linker flags and library settings based on platform
extra_compile_args = ["-DSMPT_STATIC"]
libraries = ["smpt"]  # Default library name without lib prefix

# Windows-specific configuration
if platform.system() == "Windows":
    # Check if we have the static library available
    static_lib_path = os.path.join(smpt_lib_path, "smpt.lib")
    if not os.path.exists(static_lib_path):
        static_lib_path = os.path.join(smpt_lib_path, "libsmpt.lib")

    # If we have a static lib, use it directly
    if os.path.exists(static_lib_path):
        print(f"Using static library: {static_lib_path}")
        # On Windows with static library, we need special linking configuration
        extra_link_args = ["/WHOLEARCHIVE:smpt"]

        # Use the library in its directory
        library_dirs = [smpt_lib_path]
    else:
        # If no static library, look for DLL
        dll_path = os.path.join(smpt_lib_path, "smpt.dll")
        if not os.path.exists(dll_path):
            dll_path = os.path.join(smpt_lib_path, "libsmpt.dll")

        if os.path.exists(dll_path):
            print(f"Using DLL: {dll_path}")
            # For DLL, we don't need special flags
            extra_link_args = []
            library_dirs = [smpt_lib_path]
        else:
            # Fallback if neither is found
            print("Warning: Could not find static library or DLL.")
            print("Attempting to use default library search path.")
            extra_link_args = []
            library_dirs = [smpt_lib_path]
else:
    # Unix-like systems (Linux/macOS)
    extra_link_args = []
    library_dirs = [smpt_lib_path]

# Call set_source with the appropriate configuration
ffi.set_source(
    "sciencemode._sciencemode",
    ("\n").join([f'#include "{header}"' for header in ROOT_HEADERS]),
    include_dirs=[
        include_dir,
        smpt_include_path1,
        smpt_include_path2,
        smpt_include_path3,
        smpt_include_path4,
    ],
    libraries=libraries,
    library_dirs=library_dirs,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    # Use py_limited_api to avoid symbol name issues when using static linking
    py_limited_api=False,
)


pycparser_args = {"use_cpp": True, "cpp_args": DEFINE_ARGS}

collector = Collector()
for header in ROOT_HEADERS:
    ast = pycparser.parse_file(os.sep.join([include_dir, header]), **pycparser_args)
    collector.visit(ast)

defines = set()
for header_path in HEADERS:
    with open(os.sep.join([include_dir, header_path])) as header_file:
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
            except Exception:
                defines.add(f"#define {match.group(1)} ...")

print(
    f"Processing {len(defines)} defines, {len(collector.typedecls)} types, "
    f"{len(collector.functions)} functions"
)

cdef = "\n".join(itertools.chain(*[defines, collector.typedecls, collector.functions]))

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

# Fix platform-specific field errors
if "serial_port_handle_" in cdef and not sys.platform.startswith("win"):
    # Remove the Windows-specific field for non-Windows platforms
    cdef = cdef.replace(
        "HANDLE serial_port_handle_;", "/* Windows only: HANDLE serial_port_handle_; */"
    )
elif "serial_port_descriptor" in cdef and sys.platform.startswith("win"):
    # Remove the Linux/macOS field for Windows
    cdef = cdef.replace(
        "int serial_port_descriptor;",
        "/* Linux/macOS only: int serial_port_descriptor; */",
    )


# Add explicit verification for enums that might be used in struct fields
# This is needed because CFFI tries to infer the size of enums and may fail
# Defining these explicitly helps CFFI understand struct layouts correctly
verification_code = """
typedef enum {
    Smpt_Result_Successful = 0,
    Smpt_Result_Transfer_Error = 1,
    Smpt_Result_Parameter_Error = 2,
    Smpt_Result_Protocol_Error = 3,
    Smpt_Result_Uc_Stim_Timeout_Error = 4,
    Smpt_Result_Emg_Timeout_Error = 5,
    Smpt_Result_Emg_Register_Error = 6,
    Smpt_Result_Not_Initialized_Error = 7,
    Smpt_Result_Hv_Error = 8,
    Smpt_Result_Demux_Timeout_Error = 9,
    Smpt_Result_Electrode_Error = 10,
    Smpt_Result_Invalid_Cmd_Error = 11,
    Smpt_Result_Demux_Parameter_Error = 12,
    Smpt_Result_Demux_Not_Initialized_Error = 13,
    Smpt_Result_Demux_Transfer_Error = 14,
    Smpt_Result_Demux_Unknown_Ack_Error = 15,
    Smpt_Result_Pulse_Timeout_Error = 16,
    Smpt_Result_Fuel_Gauge_Error = 17,
    Smpt_Result_Live_Signal_Error = 18,
    Smpt_Result_File_Transmission_Timeout = 19,
    Smpt_Result_File_Not_Found = 20,
    Smpt_Result_Busy = 21,
    Smpt_Result_File_Error = 22,
    Smpt_Result_Flash_Erase_Error = 23,
    Smpt_Result_Flash_Write_Error = 24,
    Smpt_Result_Unknown_Controller_Error = 25,
    Smpt_Result_Firmware_Too_Large_Error = 26,
    Smpt_Result_Fuel_Gauge_Not_Programmed = 27,
    Smpt_Result_Pulse_Low_Current_Error = 28,
    Smpt_Result_Last_Item = 29
} Smpt_Result;
"""

# Add the verification code to the beginning of our CFFI definitions
cdef = verification_code + cdef

# Define the CFFI interface with the combined definitions
# Use override=True to handle duplicate definitions (especially for Smpt_Result)
ffi.cdef(cdef, override=True)


# Create a context manager class for managing CFFI resources
class CFFIResourceManager:
    """Context manager for CFFI resources to ensure proper cleanup."""

    def __init__(self, resource, destructor=None):
        """Initialize with a CFFI resource and optional destructor function.

        Args:
            resource: CFFI resource to manage
            destructor: Optional function to call for cleanup
        """
        self.resource = resource
        self.destructor = destructor

    def __enter__(self):
        """Return the resource when entering the context."""
        return self.resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the resource when exiting the context."""
        if self.destructor and self.resource:
            try:
                self.destructor(self.resource)
            except Exception as e:
                print(f"Error during resource cleanup: {e}")
        elif hasattr(ffi, "release") and self.resource:
            try:
                ffi.release(self.resource)
            except Exception as e:
                print(f"Error releasing resource: {e}")
        self.resource = None
        return False  # Don't suppress exceptions


# Memory management helpers
def managed_new(ctype, init=None, destructor=None, size=0):
    """Create a new CFFI object with automatic memory management.

    Args:
        ctype: C type to allocate
        init: Initial value
        destructor: Custom destructor function (optional)
        size: Size hint for garbage collector (optional)

    Returns:
        CFFI object with garbage collection
    """
    if init is not None:
        obj = ffi.new(ctype, init)
    else:
        obj = ffi.new(ctype)

    if destructor:
        return ffi.gc(obj, destructor, size)
    return obj


def managed_buffer(cdata, size=None):
    """Create a managed buffer from CFFI data.

    Args:
        cdata: CFFI data to create buffer from
        size: Size of the buffer in bytes (optional)

    Returns:
        A context manager that yields a buffer object
    """
    buf = ffi.buffer(cdata, size)
    return CFFIResourceManager(buf)


# Function to get the library configuration, initialized only once
def get_smpt_config():
    """Get the SMPT library configuration, initializing it only once.

    Returns:
        dict: Configuration dictionary with paths and platform info
    """
    return ffi.init_once(_init_smpt_lib, "smpt_init")


# String conversion utilities
def to_bytes(value):
    """Convert a Python string or bytes to bytes object.

    Args:
        value: String or bytes to convert

    Returns:
        bytes: Python bytes object
    """
    if isinstance(value, str):
        return value.encode("utf-8")
    elif isinstance(value, bytes):
        return value
    else:
        return str(value).encode("utf-8")


def from_cstring(cdata):
    """Convert a C string to a Python string.

    Args:
        cdata: CFFI char* data

    Returns:
        str: Python string
    """
    if cdata == ffi.NULL:
        return None

    # Get the C string as bytes first
    byte_str = ffi.string(cdata)

    # Convert to Python string
    if isinstance(byte_str, bytes):
        return byte_str.decode("utf-8", errors="replace")
    return byte_str  # Already a string in Python 3


def to_c_array(data_type, py_list):
    """Convert a Python list to a C array of the specified type.

    Args:
        data_type: C data type (e.g., "int[]")
        py_list: Python list to convert

    Returns:
        CFFI array object
    """
    if not py_list:
        return ffi.NULL

    arr = ffi.new(data_type, len(py_list))
    for i, value in enumerate(py_list):
        arr[i] = value

    return arr


def from_c_array(cdata, length, item_type=None):
    """Convert a C array to a Python list.

    Args:
        cdata: CFFI array data
        length: Length of the array
        item_type: Optional type conversion function

    Returns:
        list: Python list with array contents
    """
    if cdata == ffi.NULL or length <= 0:
        return []

    result = [cdata[i] for i in range(length)]

    if item_type:
        result = [item_type(item) for item in result]

    return result


# Debugging feature: Write the generated C definitions to a file
# This can be enabled for troubleshooting CFFI binding issues
if False:
    file = open("sciencemode.cdef", "w")
    file.write(cdef)
    file.close()
