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

class Users(users_pb2_grpc.UsersServicer):
    def LoginUserAccount(self, request, context):
        username, password = request.username, request.password

        # if db doesn't exist, return false
        if not os.path.exists("userDB.json"):
            return users_pb2.LoginUserReply(success=False)

        # check if there is matching user
        json_db_file = open("userDB.json", "r+")
        user_entries = json.load(json_db_file)
        user = user_entries[username]

        # user doesn't exist
        if not user:
            return self.InvalidCredentialsError()

        stored_hash = user["password"]
        is_valid_creditials = bcrypt.checkpw(password.encode(), stored_hash.encode())

        if is_valid_creditials:
            
            user["token"] = self.GenerateAuthToken()
            user["login_time"] = time.time()
            user_entries[username] = user

            self.WriteToDB(user_entries)
            
            return users_pb2.LoginUserReply(success=True, token=user["token"])
        
        return self.InvalidCredentialsError()
            

    def InvalidCredentialsError(self):
        return users_pb2.LoginUserReply(success=False, token="")

    def GenerateAuthToken(self):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(16))

    def CreateUserAccount(self, request, context):  

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

        self.WriteToDB(user_entries)

        return users_pb2.CreateUserReply(success=True) 

    def WriteToDB(self, user_entries):
        # This will erase everything that was in the json file and add the proper dictionary list of users
        new_json = open("userDB.json", "w")
        json.dump(user_entries, new_json)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_pb2_grpc.add_UsersServicer_to_server(Users(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()