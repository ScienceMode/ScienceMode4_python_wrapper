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

INCLUDE_PATTERN = re.compile(r"(-I)?(.*ScienceMode)")
DEFINE_PATTERN = re.compile(r"^#define\s+(\w+)\s+\(?([\w<|.]+)\)?", re.M)
DEFINE_BLACKLIST = {
    "main",
}

# Try to find the include directory in different locations
devel_root_candidates = [
    os.path.abspath("./smpt/ScienceMode_Library/include"),
    os.path.abspath("./smpt/ScienceMode_Library"),
    os.path.abspath("../smpt/ScienceMode_Library/include"),
    os.path.abspath("../smpt/ScienceMode_Library"),
    os.path.abspath("../include/ScienceMode4"),
    os.path.abspath("./include/ScienceMode4"),
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
smpt_lib_path = os.path.abspath("./lib")

# Create lib directory if it doesn't exist
if not os.path.exists(smpt_lib_path):
    try:
        print(f"Creating lib directory: {smpt_lib_path}")
        os.makedirs(smpt_lib_path, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create lib directory: {e}")

# Check for SMPT library existence
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
    ("\n").join([f'#include "{header}"' for header in ROOT_HEADERS]),
    include_dirs=[
        include_dir,
        smpt_include_path1,
        smpt_include_path2,
        smpt_include_path3,
        smpt_include_path4,
    ],
    libraries=["smpt"],  # Library name without lib prefix
    library_dirs=[smpt_lib_path],  # Using the absolute path variable
    # Use static linking for all platforms
    extra_compile_args=["-DSMPT_STATIC"],
    # Modify linking flags to avoid static linking issues
    extra_link_args=[] if platform.system() != "Windows" else ["/WHOLEARCHIVE:smpt"],
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


ffi.cdef(cdef)

if False:
    file = open("sciencemode.cdef", "w")
    file.write(cdef)
    file.close()
