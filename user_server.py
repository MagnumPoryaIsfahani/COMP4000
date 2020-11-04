from concurrent import futures
import logging
import grpc
import os

import users_pb2
import users_pb2_grpc
import status_codes

import json
import bcrypt
import random
import string
import time
import secrets

# how long the token will remain valid in seconds
TOKEN_LIFETIME = 30

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
        
        return users_pb2.LoginUserReply(success=True, token=user["token"])

    def updateUserAccount(self, request, context):
        username = request.username

        # checks if db exists and if its empty, returns 404 if not found/empty
        try:
            user = self.fetchUserFromDB(username)
        except:
            return users_pb2.UpdateUserReply(code=status_codes.NOT_FOUND)

        # check that token is valid
        if user.get("token") != request.token:
            return users_pb2.UpdateUserReply(code=status_codes.UNAUTHENTICATED)

        # check if token has expired
        if user.get("login_time", 0) + TOKEN_LIFETIME < time.time():
            return users_pb2.UpdateUserReply(code=status_codes.DEADLINE_EXCEEDED)
        
        # checks to see if new password is the same as old password
        stored_hash = user.get("password")
        is_same_password = bcrypt.checkpw(request.password.encode(), stored_hash.encode())
        if is_same_password:
            return users_pb2.UpdateUserReply(code=status_codes.ALREADY_EXISTS)

        # hashes the new password and invalidates existing token by setting login_time to 0
        hashed_binary = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())
        password = hashed_binary.decode(encoding="utf-8")
        updatedUser = {"password": password, "login_time": 0}

        #throw the updated account into the temp dictionary
        self.saveUserToDB(updatedUser, username)

        return users_pb2.UpdateUserReply(code=status_codes.OK)
                
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
            self.saveUserToDB({'password': password}, username)
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

    def fsGetAttr(self, request, context):
        st = os.lstat(request.path)
        data = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        return users_pb2.GetAttrReponse(data=json.dumps(data))

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

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_pb2_grpc.add_UsersServicer_to_server(Users(), server)
    server.add_insecure_port('[::]:10001')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
