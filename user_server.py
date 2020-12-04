from concurrent import futures
from fuse import FuseOSError
import logging
import grpc
import os
import threading

import users_pb2
import users_pb2_grpc

import json
import bcrypt
import random
import string
import time
import secrets
import threading

# how long the token will remain valid in seconds
TOKEN_LIFETIME = 30
lock = threading.Lock()

class Users(users_pb2_grpc.UsersServicer):
    
    def loginUserAccount(self, request, context):
        username, password = request.username, request.password

        # get user from DB
        try:
            user = self.fetchUserFromDB(username)
        except:
            return users_pb2.LoginUserReply(success=False)

        stored_hash = user["password"]
        is_valid_creditials = bcrypt.checkpw(password.encode(), stored_hash.encode())
        
        # invalid password
        if not is_valid_creditials:
            return users_pb2.LoginUserReply(success=False)

        # logging in
        print("valid creds")
        if not user.get("login_time", False):
            user["token"] = secrets.token_urlsafe(8)
            print("first token issued")
        elif user["login_time"] + TOKEN_LIFETIME < time.time():
            user["token"] = secrets.token_urlsafe(8)
            print("token expired, new one issued")
        
        user["login_time"] = time.time() + TOKEN_LIFETIME
        print("login time updated")

        self.saveUserToDB(user, username)
        
        return users_pb2.LoginUserReply(success=True, token=user["token"], username=username)

    def updateUserAccount(self, request, context):
        username = request.username

        # checks if db exists and if its empty, returns 404 if not found/empty
        try:
            user = self.fetchUserFromDB(username)
        except:
            return users_pb2.UpdateUserReply(code=grpc.StatusCode.NOT_FOUND.value[0])

        # check that token is valid -- Now done in checkToken
        #if user.get("token") != request.token:
        #    return users_pb2.UpdateUserReply(code=grpc.StatusCode.UNAUTHENTICATED.value[0])

        #now done in stub.checkToken, before allowing the rest of the function to proceed
        # check if token has expired
        #if user.get("login_time", 0) + TOKEN_LIFETIME < time.time():
        #    return users_pb2.UpdateUserReply(code=grpc.StatusCode.DEADLINE_EXCEEDED.value[0])
        
        # checks to see if new password is the same as old password
        stored_hash = user.get("password")
        is_same_password = bcrypt.checkpw(request.password.encode(), stored_hash.encode())
        if is_same_password:
            return users_pb2.UpdateUserReply(code=grpc.StatusCode.ALREADY_EXISTS.value[0])

        # hashes the new password and invalidates existing token by setting login_time to 0
        hashed_binary = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())
        password = hashed_binary.decode(encoding="utf-8")
        updatedUser = {"password": password, "login_time": 0, "mount_perms":user["mount_perms"]}
        
        #throw the updated account into the temp dictionary
        self.saveUserToDB(updatedUser, username)

        return users_pb2.UpdateUserReply(code=grpc.StatusCode.OK.value[0])
                
    def createUserAccount(self, request, context):  
        # Create a salt and using bcrypt, hash the user's credentials
        hashed_binary = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())
        password = hashed_binary.decode(encoding="utf-8")
        username = request.username

        try:
            self.fetchUserFromDB(username)
            return users_pb2.CreateUserReply(success=False)
        except:
            # creating account
            self.saveUserToDB({'password': password, 'mount_perms':'0'}, username)
            return users_pb2.CreateUserReply(success=True) 

    def deleteUserAccount(self, request, context):
        username = request.username
        try:
            user = self.fetchUserFromDB(username)
        except:
            return users_pb2.DeleteUserReply(success=False)

        if user and user.get("token") == request.token and time.time() < user.get("login_time", 0) + TOKEN_LIFETIME:
            self.saveUserToDB(None, username)
            return users_pb2.DeleteUserReply(success=True)
        
        return users_pb2.DeleteUserReply(success=False)

    def displayTree(self, request, context):
        
        tree = os.popen('tree /home/student/fuse').read()
        return users_pb2.DisplayTreeReply(tree=tree)

    # Filesystem methods
    # ==================
    def fsAccess(self, request, context):
        if not os.access(request.path, request.mode):
            return users_pb2.JsonReply(error=True)
        return users_pb2.JsonReply(error=False)

    def fsChmod(self, request, context):
        data = os.chmod(request.path, request.mode)
        return users_pb2.JsonReply(data=json.dumps(data))
    
    def fsChown(self, request, context):
        data = os.chown(request.path, request.uid, request.gid)
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsGetAttr(self, request, context):
        error = False
        data = {}
        try:
            st = os.lstat(request.path)
            data = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        except:
            error = True
        return users_pb2.JsonReply(data=json.dumps(data), error=error)

    def fsReadDir(self, request, context):
        dirents = ['.', '..']
        
        if os.path.isdir(request.path):
            dirents.extend(os.listdir(request.path))
        
        return users_pb2.JsonReply(data=json.dumps(dirents))
    
    def fsRmDir(self, request, context):
        data = os.rmdir(request.path)
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsMkDir(self, request, context):
        data = os.mkdir(request.path, request.mode)
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsStat(self, request, context):
        stv = os.statvfs(request.path)
        data = dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsUtimens(self, request, context):
        data = os.utime(request.path,(request.aTime, request.mTime))
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsUnlink(self, request, context):
        global lock 
        lock.acquire()
        data = os.unlink(request.path)
        lock.release()
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsSymlink(self, request, context):
        data = os.symlink(request.target, request.name)
        return users_pb2.JsonReply(data=json.dumps(data))
    
    def fsRename(self, request, context):
        data = os.rename(request.oldPath, request.newPath)
        return users_pb2.JsonReply(data=json.dumps(data))
    
    def fsLink(self, request, context):
        data = os.link(request.name, request.target)
        return users_pb2.JsonReply(data=json.dumps(data))

    def fsFlock(self, request, context):
        data = os.flock(request.fileDescriptor, request.lockOperation)
        return users_pb2.JsonReply(data=json.dumps(data))

    # File methods
    # ============
    def fileOpen(self, request, context):
        data = os.open(request.path, request.flags)       
        return users_pb2.JsonReply(data=json.dumps(data))

    def fileCreate(self, request, context):
        data = os.open(request.path, os.O_RDWR | os.O_CREAT, request.mode)
        return users_pb2.JsonReply(data=json.dumps(data))

    def fileRead(self, request, context):
        os.lseek(request.fh, request.offset, os.SEEK_SET)
        data = os.read(request.fh, request.length)
        return users_pb2.ReadReply(data=data)

    def fileWrite(self, request, context):  
        global lock 
        lock.acquire()
        os.lseek(request.fh, request.offset, os.SEEK_SET)
        reply = users_pb2.JsonReply(data=json.dumps(os.write(request.fh, request.buf)))
        lock.release()
        return reply

    def fileFlush(self, request, context):
        return users_pb2.JsonReply(data=json.dumps(os.fsync(request.fh)))

    def fileRelease(self, request, context):
        return users_pb2.JsonReply(data=json.dumps(os.close(request.fh)))        

    def saveUserToDB(self, user, username):
        # initialize db if its empty
        if not os.path.exists("userDB.json") or os.stat("userDB.json").st_size == 0:
            user_entries = {}
        else:
            read_file = open("userDB.json", "r+")
            user_entries = json.load(read_file)
            read_file.close()

        if user:
            user_entries[username] = user
        else:
            user_entries.pop(username, None)

        write_file = open("userDB.json", 'w+')
        json.dump(user_entries, write_file)
        write_file.close()

    def auth2Mount(self, request, context):
        user = self.fetchUserFromDB(request.username)
        #print("Checking "+request.username+" mounting permissions")
        # user must have previously logged in to get a token
        if not user.get("login_time",False):
            return users_pb2.auth2MountReply(success=1)

        if user["token"] != request.token:
            return users_pb2.auth2MountReply(success=2)

        if user["login_time"] + TOKEN_LIFETIME < time.time():    
            return users_pb2.auth2MountReply(success=3)
        
        if user["mount_perms"] == '1':
            return users_pb2.auth2MountReply(success=4)

        return users_pb2.auth2MountReply(success=0)
    def checkToken(self, request, context):
        user = self.fetchUserFromDB(request.username)
        if user.get("token",0) == request.token and user.get("login_time",0)+TOKEN_LIFETIME > time.time():
            user["login_time"] = time.time()
            saveUserToDB(user,request.username)
            return users_pb2.CheckTokenReply(success=True)
        return users_pb2.CheckTokenReply(success=False)

    def fetchUserFromDB(self, username):
        # error if db doesn't exist or is empty
        if not os.path.exists("userDB.json") or os.stat("userDB.json").st_size == 0:
            raise Exception()

        # check if there is matching user
        db_file = open("userDB.json", "r+")
        user_entries = json.load(db_file)
        user = user_entries.get(username)
        db_file.close()

        # error if user doesn't exist
        if not user:
            raise Exception()

        return user

    # could this be added onto the login reply?    
    def clearanceLevel(self, request, context):
        f = open("admins.txt",'r')
        for line in f:
            if line[:-1] == request.username:
                return users_pb2.ClearanceLevelReply(level=0)
        f.close()
        f = open("trusted.txt",'r')
        for line in f:
            if line[:-1] == request.username:
                return users_pb2.ClearanceLevelReply(level=1)
        return users_pb2.ClearanceLevelReply(level=2)

    def changeMountPerms(self, request, context):
        user = self.fetchUserFromDB(request.targetName)
        user["mount_perms"] = request.value
        self.saveUserToDB(user, request.targetName)
        return users_pb2.ChangeMountPermsReply(success=True)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_pb2_grpc.add_UsersServicer_to_server(Users(), server)
    
    with open('server.key','rb') as f:
        private_key = f.read()
    with open('server.crt','rb') as f:
        certificate_chain = f.read()

    server_creds = grpc.ssl_server_credentials(((private_key,certificate_chain,),))

    #server.add_insecure_port('[::]:10001')
    server.add_secure_port('[::]:10002',server_creds)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
