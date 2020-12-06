#!/usr/bin/env python

from __future__ import with_statement
from fuse import FuseOSError, Operations

import os
import sys
import json
import errno
import signal

import users_pb2
import datetime

IS_DEBUG = True

class Passthrough(Operations):
    def __init__(self, root, stub, username, token):
        self.root = root
        self.stub = stub
        self.username = username
        self.token = token
        print(self.username)

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
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[access]", path, mode)
        path = self._full_path(path)

        response = self.stub.fsAccess(users_pb2.AccessRequest(path=path, mode=mode,username=self.username))

        if response.error:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[chmod]")
        response = self.stub.fsChmod(users_pb2.ChmodRequest(path=self._full_path(path), mode=mode,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return json.loads(response.data)

    def chown(self, path, uid, gid):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[chown]")
        response = self.stub.fsChown(users_pb2.ChownRequest(path=self._full_path(path), uid=uid, gid=gid,username=self.username))
        return json.loads(response.data)
        

    def getattr(self, path, fh=None):
        if IS_DEBUG: print("[getattr]", path, fh)
        path = self._full_path(path)
        response = self.stub.fsGetAttr(users_pb2.GetAttrRequest(path=path, fh=fh,username=self.username))
        
        if response.error:
            raise FuseOSError(2)

        return json.loads(response.data)

    def readdir(self, path, fh):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[readdir]", path, fh)
        path = self._full_path(path)
        response = self.stub.fsReadDir(users_pb2.ReadDirRequest(path=path,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCESS)

        dirents = json.loads(response.data)

        for r in dirents:
            yield r

    def readlink(self, path):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[readlink]")
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[mknod]")
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[rmdir]")
        full_path = self._full_path(path)
        response = self.stub.fsRmDir(users_pb2.RmDirRequest(path=full_path,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return json.loads(response.data)

    def mkdir(self, path, mode):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[mkdir]")
        full_path = self._full_path(path)
        response = self.stub.fsMkDir(users_pb2.MkDirRequest(path=full_path, mode=mode,username=self.username))
        return json.loads(response.data)

    def statfs(self, path):
        if IS_DEBUG: print("[statfs]", path)
        full_path = self._full_path(path)
        response = self.stub.fsStat(users_pb2.StatRequest(path=full_path,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        print("STAT DATA", response.data)

        return json.loads(response.data)


    def unlink(self, path):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[unlink]")
        response = self.stub.fsUnlink(users_pb2.UnlinkRequest(path=self._full_path(path),username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)

    def utimens(self, path, times=None):
        if IS_DEBUG: print("[utimens]", path, json.dumps(times))
        if times != None:
            accessTime = times[0]
            modifiedTime = times[1]
            response = self.stub.fsUtimens(users_pb2.UtimeNsRequest(path=self._full_path(path),aTime=accessTime,mTime=modifiedTime,username=self.username))
        else:
            currentTime = datetime.now().timestamp()
            response = self.stub.fsUtimens(users_pb2.UtimeNsRequest(path=self._full_path(path),aTime=currentTime,mTime=currentTime,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)

    def symlink(self, name, target):
        if IS_DEBUG: print("[symlink]")
        response = self.stub.fsSymlink(users_pb2.SymlinkRequest(target = target, name=self._full_path(name),username=self.username)) 
        if response.error:
            raise FuseOSError(errno.EACCES)

    def rename(self, old, new):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[rename]")
        response = self.stub.fsRename(users_pb2.RenameRequest(oldPath = self._full_path(old), newPath=self._full_path(new),username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)


    def link(self, target, name):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[link]")
        response = self.stub.fsLink(users_pb2.LinkRequest(name = self._full_path(name), target=self._full_path(target),username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)

    def flock(self,fd, operation):
        if IS_DEBUG: print("[flock]")
        
        response = self.stub.fsFlock(users_pb2.FlockRequest(fileDescriptor = fd, lockOperation= operation))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return response

    # File methods
    # ============

    def open(self, path, flags):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
         
        
        if IS_DEBUG: print("[open]", path, flags)
        full_path = self._full_path(path)
        response = self.stub.fileOpen(users_pb2.OpenRequest(path=full_path, flags=flags,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        
        return json.loads(response.data)

    def create(self, path, mode, fi=None):
        if IS_DEBUG: print("[create]", path, mode, fi)
        full_path = self._full_path(path)
        response = self.stub.fileCreate(users_pb2.CreateRequest(path=full_path, mode=mode, fi=fi,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        
        print("CREATE DATA:", response.data)
        return json.loads(response.data)
        
    def read(self, path, length, offset, fh):
        if IS_DEBUG: print("[read]", path, length, offset, fh)
        response = self.stub.fileRead(users_pb2.ReadRequest(length=length, offset=offset, fh=fh,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return response.data

    def write(self, path, buf, offset, fh):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGKILL)
        if IS_DEBUG: print("[write]", path, buf, offset, fh)
        full_path = self._full_path(path)
        response = self.stub.fileWrite(users_pb2.WriteRequest(path=full_path, buf=buf, offset=offset, fh=fh,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return json.loads(response.data)

    def truncate(self, path, length, fh=None):
        if IS_DEBUG: print("[truncate]")
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        if IS_DEBUG: print("[flush]")
        response = self.stub.fileFlush(users_pb2.FlushRequest(path=path, fh=fh,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return json.loads(response.data)

    def release(self, path, fh):
        if IS_DEBUG: print("[release]")
        response = self.stub.fileRelease(users_pb2.ReleaseRequest(path=path, fh=fh,username=self.username))
        if response.error:
            raise FuseOSError(errno.EACCES)
        return json.loads(response.data)

    def fsync(self, path, fdatasync, fh):
        valid=self.stub.checkToken(users_pb2.CheckTokenRequest(username=self.username, token=self.token))
        if not valid.success:
            print("token Expired, unmounting fileSystem")
            os.kill(os.getpid(),signal.SIGINT)
        if IS_DEBUG: print("[fsync]")
        return self.flush(path, fh)
