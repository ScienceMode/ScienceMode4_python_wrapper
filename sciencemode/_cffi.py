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
project_root = os.path.dirname(current_dir)

# Print for debugging
print(f"Found ScienceMode in: {project_root}")

# Setup paths based on the structure
smpt_submodule_path = os.path.join(project_root, "smpt", "ScienceMode_Library")
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

INCLUDE_PATTERN = re.compile(r"(-I)?(.*ScienceMode)")
DEFINE_PATTERN = re.compile(r"^#define\s+(\w+)\s+\(?([\w<|.]+)\)?", re.M)
DEFINE_BLACKLIST = {
    "main",
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
            # Avoid problematic macros that can cause unbalanced conditionals
            "-U_MSC_VER",  # Don't pretend to be MSVC on macOS
            "-U_WIN32",
            "-UWIN32",
            # Define away problematic Apple-specific macros
            "-D__builtin_available(...)=1",
            "-D__has_feature(x)=0",
            "-D__has_extension(x)=0",
            "-D__has_attribute(x)=0",
            # Let macOS use its standard bool handling instead of our bool redefinition
            "-Ubool",  # Undefine our bool override
            "-U_Bool",  # Undefine our _Bool override
            "-Utrue",  # Undefine our true override
            "-Ufalse",  # Undefine our false override
        ]
    )

FUNCTION_BLACKLIST = {}

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
    ("\n").join(f'#include "{header}"' for header in ROOT_HEADERS),
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

ffi.cdef(cdef)

print("CFFI configuration completed successfully!")

# Optional: save for debugging
if False:
    with open("sciencemode.cdef", "w", encoding="utf-8") as file:
        file.write(cdef)
