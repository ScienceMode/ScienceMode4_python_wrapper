from __future__ import absolute_import

from sciencemode._sciencemode import lib, ffi

for __name in dir(lib):
    globals()[__name] = getattr(lib, __name)