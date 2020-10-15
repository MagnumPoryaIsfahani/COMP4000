from concurrent import futures
import logging
import grpc
import os

import users_pb2
import users_pb2_grpc

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

        # if db doesn't exist, return false
        if not os.path.exists("userDB.json"):
            return users_pb2.LoginUserReply(success=False)

        # check if there is matching user
        json_db_file = open("userDB.json", "r+")
        user_entries = json.load(json_db_file)
        user = user_entries.get(username)

        # user doesn't exist
        if not user:
            return self.invalidCredentialsError()

        stored_hash = user["password"]
        is_valid_creditials = bcrypt.checkpw(password.encode(), stored_hash.encode())
        
        if is_valid_creditials: 
            print("valid creds")
            if not user.get("login_time",False):
                user["login_time"] = time.time() + TOKEN_LIFETIME
                user["token"] = secrets.token_urlsafe(8)
                print("new token")
            elif user["login_time"] > time.time():
                user["login_time"] = time.time() + TOKEN_LIFETIME
                print("login time updated")
            else:
                user["login_time"] = time.time() + TOKEN_LIFETIME
                user["token"] = secrets.token_urlsafe(8)
                print("new valid token.")

            user_entries[username] = user
            json_db_file.close()
            self.writeToDB(user_entries)
            
            return users_pb2.LoginUserReply(success=True, token=user["token"])
        
        return self.invalidCredentialsError()

    def updateUserAccount(self, request, context):
        #Checks if db exists and if its empty, returns 404 if not found/empty
        if not os.path.exists("userDB.json"):
            return users_pb2.UpdateUserReply(code=404, token=request.token)

        json_db_file = open("userDB.json", "r+")

        if os.stat("userDB.json").st_size == 0:
            return users_pb2.UpdateUserReply(code=404, token=request.token)

        user_entries = json.load(json_db_file)

        #finds the user to update
        #There must be a better way to do this as this has a run time of O(n)... Maybe not important for now, we could just pass the username around everywhere in client if need be.
        for user in user_entries:
            if user_entries[user].get("token") == request.token:
                if user_entries[user].get("login_time", 0) + TOKEN_LIFETIME > time.time():
                    #checks to see if new password is the same as old password
                    stored_hash = user_entries[user].get("password")
                    is_same_password = bcrypt.checkpw(request.password.encode(), stored_hash.encode())

                    if is_same_password:
                        return users_pb2.UpdateUserReply(code=405, token=request.token)

                    #hashes the new password
                    hashed_binary = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())
                    password = hashed_binary.decode(encoding="utf-8")
                    updatedPassword = {"password": password}

                    #throw the updated account into the temp dictionary
                    user_entries[user].update(updatedPassword)
                    json_db_file.close()

                    #update the DB with the temp dictionary
                    self.writeToDB(user_entries)
                    return users_pb2.UpdateUserReply(code=200, token=request.token)
                else:
                    return users_pb2.UpdateUserReply(code=408 , token=request.token)

        return users_pb2.UpdateUserReply(code=401 , token=request.token)

    def createUserAccount(self, request, context):  

        # Create a salt and using bcrypt, hash the user's credentials
        hashed_binary = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt())
        password = hashed_binary.decode(encoding="utf-8")
        username = request.username
        
        # Check if file exists, if it doesnt create a new one and allow it to be readable/writable
        if os.path.exists("userDB.json"):
            json_db_file = open("userDB.json", "r+") 
        else:
            json_db_file = open("userDB.json", "w+") 

        # If file size is 0, it means its empty and we can fill it up
        if os.stat("userDB.json").st_size == 0:
            # Create dictioanry of users
            user_entries = {}
            user_entries[username] = {"password":password}     
        else:
            # Load json file and append new user to the end 
            user_entries = json.load(json_db_file)
            # Check to see if the username the user gave already exists as a key in the dictionary 
            if username in user_entries:
                return users_pb2.CreateUserReply(success=False)
            else:
                user_entries[username] = {"password": password}

        self.writeToDB(user_entries)

        return users_pb2.CreateUserReply(success=True) 

    def deleteUserAccount(self,request,context):
        if not os.path.exists("userDB.json"):
            print("file not found")
            return users_pb2.DeleteUserReply(success=False)
        json_db_file = open("userDB.json","r+")
        if os.stat("userDB.json").st_size == 0:
            print("no users in file")
            return users_pb2.DeleteUserReply(success=False)
        user_entries = json.load(json_db_file)
        if user_entries[request.username].get("token") == request.token and user_entries[request.username].get("login_time", 0) + TOKEN_LIFETIME > time.time():
            del user_entries[request.username]
            json_db_file.close()
            self.writeToDB(user_entries)
            return users_pb2.DeleteUserReply(success=True)
        
        return users_pb2.DeleteUserReply(success=False)
    
    def invalidCredentialsError(self):
        return users_pb2.LoginUserReply(success=False, token="")

    def writeToDB(self, user_entries):
        # This will erase everything that was in the json file and add the proper dictionary list of users
        new_json = open("userDB.json", "w")
        json.dump(user_entries, new_json)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_pb2_grpc.add_UsersServicer_to_server(Users(), server)
    server.add_insecure_port('[::]:10001')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
