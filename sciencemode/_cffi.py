# -*- coding: utf-8 -*-

from cffi import FFI
from subprocess import check_output
import re
import os
import pycparser
import json
import itertools
import platform
import sys
from pycparser import c_ast
from pycparser.c_generator import CGenerator

INCLUDE_PATTERN = re.compile(r'(-I)?(.*ScienceMode)')
DEFINE_PATTERN = re.compile(r'^#define\s+(\w+)\s+\(?([\w<|.]+)\)?', re.M)
DEFINE_BLACKLIST = {
    'main',
    }

devel_root = os.path.abspath("./smpt/ScienceMode_Library")
include_dir = os.path.join(devel_root, "include")

smpt_lib_path = os.path.abspath("./lib")

smpt_include_path1 = os.path.join(include_dir, "general")
smpt_include_path2 = os.path.join(include_dir, "low-level")
smpt_include_path3 = os.path.join(include_dir, "mid-level")
smpt_include_path4 = os.path.join(include_dir, "dyscom-level")

# define GCC specific compiler extensions away
DEFINE_ARGS = [
    '-D_WIN32',
    '-D__attribute__(x)=',
    '-D__inline=',
    '-D__restrict=',
    '-D__extension__=',
    '-D__GNUC_VA_LIST=',
    '-D__inline__=',
    '-D__forceinline=',
    '-D__volatile__=',
    '-D__MINGW_NOTHROW=',
    '-D__nothrow__=',
    '-DCRTIMP=',
    '-DSDL_FORCE_INLINE=',
    '-DDOXYGEN_SHOULD_IGNORE_THIS=',
    '-D_PROCESS_H_=',
    '-U__GNUC__',
    '-Ui386',
    '-U__i386__',
    '-U__MINGW32__',
    '-DNT_INCLUDED',
    '-D_MSC_VER=1900',
    '-L'+smpt_lib_path,
    '-Iutils/fake_libc_include',
    '-Iutils/fake_windows_include',
    '-I'+smpt_include_path1,
    '-I'+smpt_include_path2,
    '-I'+smpt_include_path3,
    '-I'+smpt_include_path4
]

FUNCTION_BLACKLIST = {

}

VARIADIC_ARG_PATTERN = re.compile(r'va_list \w+')
ARRAY_SIZEOF_PATTERN = re.compile(r'\[[^\]]*sizeof[^\]]*]')

HEADERS = [
    'general/smpt_client_data.h',
    'general/smpt_definitions_data_types.h',
    'general/smpt_client_cmd_lists.h',
    'general/smpt_definitions.h',
    'general/smpt_definitions_internal.h',
    'general/smpt_messages.h',
    'general/packet/smpt_packet_general.h',
    'general/packet/smpt_packet_internal.h',
    'general/packet/smpt_packet_validity.h',
    'general/packet/smpt_packet_utils.h',
    'general/packet/smpt_packet_client.h',
    'general/packet/smpt_packet_server.h',
    'general/packet_input_buffer/smpt_packet_input_buffer.h',
    'general/packet_input_buffer/smpt_packet_input_buffer_definitions.h',
    'general/packet_input_buffer/smpt_packet_input_buffer_internal.h',
    'general/packet_output_buffer/smpt_packet_output_buffer.h',
    'general/serial_port/smpt_serial_port.h',
    'general/serial_port/smpt_serial_port_windows.h',
    'general/serial_port/smpt_serial_port_linux.h',
    'general/smpt_definitions_file_transfer.h',
    'general/smpt_file.h',
    'general/smpt_packet_number_generator.h',
    'general/smpt_definitions_power.h',
    'general/smpt_client_power.h',
    'general/smpt_client_utils.h',
    'low-level/smpt_ll_definitions.h',
    'low-level/smpt_ll_packet_client.h',
    'low-level/smpt_ll_packet_server.h',
    'low-level/smpt_ll_packet_validity.h',
    'low-level/smpt_ll_definitions_data_types.h',
    'low-level/smpt_ll_messages.h',
    'mid-level/smpt_ml_definitions.h',
    'mid-level/smpt_ml_packet_client.h',
    'mid-level/smpt_ml_packet_server.h',
    'mid-level/smpt_ml_packet_validity.h',
    'mid-level/smpt_ml_packet_utils.h',
    'mid-level/smpt_ml_definitions_data_types.h',
    'dyscom-level/smpt_dl_definitions.h',
    'dyscom-level/smpt_dl_packet_client.h',
    'dyscom-level/smpt_dl_packet_server.h',
    'dyscom-level/smpt_dl_packet_validity.h',
    'dyscom-level/smpt_dl_packet_utils.h',
    'dyscom-level/smpt_dl_definitions_data_types.h',
]

ROOT_HEADERS = [
    'general/smpt_client.h',
    'dyscom-level/smpt_dl_client.h',
    'low-level/smpt_ll_client.h',
    'mid-level/smpt_ml_client.h',
]



class Collector(c_ast.NodeVisitor):

    def __init__(self):
        self.generator = CGenerator()
        self.typedecls = []
        self.functions = []

    def process_typedecl(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            typedecl = '{};'.format(self.generator.visit(node))
            typedecl = ARRAY_SIZEOF_PATTERN.sub('[...]', typedecl)
            if typedecl not in self.typedecls:
                self.typedecls.append(typedecl)

    def sanitize_enum(self, enum):
        for name, enumeratorlist in enum.children():
            for name, enumerator in enumeratorlist.children():
                enumerator.value = c_ast.Constant('dummy', '...')
        return enum

    def visit_Typedef(self, node):
        coord = os.path.abspath(node.coord.file)
        if node.coord is None or coord.find(include_dir) != -1:
            if ((isinstance(node.type, c_ast.TypeDecl) and
                 isinstance(node.type.type, c_ast.Enum))):
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
            decl = '{};'.format(self.generator.visit(node))
            decl = VARIADIC_ARG_PATTERN.sub('...', decl)
            if decl not in self.functions:
                self.functions.append(decl)


ffi = FFI()




ffi.set_source(
 "sciencemode._sciencemode",
 ('\n').join('#include "%s"' % header for header in ROOT_HEADERS),
 include_dirs = [include_dir, smpt_include_path1, smpt_include_path2, smpt_include_path3, smpt_include_path4],
 libraries = ['libsmpt'],
 library_dirs = ["./lib"],
)



pycparser_args = {
    'use_cpp': True,
    'cpp_args': DEFINE_ARGS
}
if sys.platform.startswith('win'):  #windows
    mingw_path = os.getenv('MINGW_PATH', default='D:\\Qt\\Tools\\mingw530_32')
    # cl_path = "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Enterprise\\VC\\Tools\\MSVC\\14.16.27023\\bin\\Hostx86\\x64\\cl.exe"
    pycparser_args['cpp_path'] = '{}\\bin\\cpp.exe'.format(mingw_path)

collector = Collector()
for header in ROOT_HEADERS:
    ast = pycparser.parse_file(os.sep.join([include_dir, header]), **pycparser_args)
    collector.visit(ast)

defines = set()
for header_path in HEADERS:
    with open(os.sep.join([include_dir, header_path]), 'r') as header_file:
        header = header_file.read()
        for match in DEFINE_PATTERN.finditer(header):
            if match.group(1) in DEFINE_BLACKLIST or match.group(1) in collector.typedecls or match.group(1) in collector.functions:
                continue
            try:
                int(match.group(2), 0)
                defines.add('#define {} {}'.format(match.group(1),
                                                   match.group(2)))
            except:
                defines.add('#define {} ...'.format(match.group(1)))

print('Processing {} defines, {} types, {} functions'.format(
    len(defines),
    len(collector.typedecls),
    len(collector.functions)
))

cdef = '\n'.join(itertools.chain(*[
    defines,
    collector.typedecls,
    collector.functions
]))

cdef = cdef.replace('[Smpt_Length_Max_Packet_Size]', '[1200]')
cdef = cdef.replace('[Smpt_Length_Packet_Input_Buffer_Rows]', '[100]')
cdef = cdef.replace('[Smpt_Length_Packet_Input_Buffer_Rows * Smpt_Length_Max_Packet_Size]', '[120000]')
cdef = cdef.replace('[Smpt_Length_Serial_Port_Chars]','[256]')
cdef = cdef.replace('[Smpt_Length_Number_Of_Acks]', '[100]')
cdef = cdef.replace('[Smpt_Length_Device_Id]', '[10]')
cdef = cdef.replace('[Smpt_Length_Points]', '[16]')
cdef = cdef.replace('[Smpt_Length_Number_Of_Channels]', '[8]')


ffi.cdef(cdef)

if False:
    file = open('sciencemode.cdef', 'w')
    file.write(cdef)
    file.close()
