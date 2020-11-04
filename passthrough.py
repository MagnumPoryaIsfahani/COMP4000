#!/usr/bin/env python

from __future__ import with_statement
from fuse import FuseOSError, Operations

import os
import sys
import json
import errno

import users_pb2

IS_DEBUG = True

class Passthrough(Operations):
    def __init__(self, root, stub):
        self.root = root
        self.stub = stub

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        if IS_DEBUG: print("[access]")
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        if IS_DEBUG: print("[chmod]")
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        if IS_DEBUG: print("[chown]")
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        if IS_DEBUG: print("[getattr]", path, fh)
        path = self._full_path(path)
        response = self.stub.fsGetAttr(users_pb2.GetAttrRequest(path=path, fh=fh))
        
        print("DATA", response.data)

        return json.loads(response.data)

    def readdir(self, path, fh):
        if IS_DEBUG: print("[readdir]", path, fh)
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        if IS_DEBUG: print("[readlink]")
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        if IS_DEBUG: print("[mknod]")
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        if IS_DEBUG: print("[rmdir]")
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        if IS_DEBUG: print("[mkdir]")
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        if IS_DEBUG: print("[statfs]")
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        if IS_DEBUG: print("[unlink]")
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        if IS_DEBUG: print("[symlink]")
        return os.symlink(target, self._full_path(name))

    def rename(self, old, new):
        if IS_DEBUG: print("[rename]")
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        if IS_DEBUG: print("[link]")
        return os.link(self._full_path(name), self._full_path(target))

    def utimens(self, path, times=None):
        if IS_DEBUG: print("[utimens]")
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        if IS_DEBUG: print("[open]", path, flags)
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        if IS_DEBUG: print("[create]")
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        if IS_DEBUG: print("[read]", path, length, offset, fh)
        os.lseek(fh, offset, os.SEEK_SET)
        return "beep beep"

    def write(self, path, buf, offset, fh):
        if IS_DEBUG: print("[write]")
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        if IS_DEBUG: print("[truncate]")
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        if IS_DEBUG: print("[flush]")
        return os.fsync(fh)

    def release(self, path, fh):
        if IS_DEBUG: print("[release]")
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        if IS_DEBUG: print("[fsync]")
        return self.flush(path, fh)
