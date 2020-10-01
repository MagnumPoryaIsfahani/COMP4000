from concurrent import futures
import logging
import grpc
import os

import users_pb2
import users_pb2_grpc

import json
import bcrypt



class Users(users_pb2_grpc.UsersServicer):
    salt = bcrypt.gensalt()
    
    def CreateUserAccount(self, request, context):  

        # Create a salt and using bcrypt, hash the user's credentials
        binary_hash_password = bcrypt.hashpw(request.password.encode("utf-8"), Users.salt)
        password = binary_hash_password.decode(encoding="utf-8")
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
                return users_pb2.CreateUserReply(message="false")
            else:
                user_entries[username] = {"password": password}

        # This will erase everything that was in the json file and add the proper dictionary list of users
        new_json = open("userDB.json", "w")
        json.dump(user_entries, new_json)
        json_db_file.close()

        return users_pb2.CreateUserReply(message="True")    

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_pb2_grpc.add_UsersServicer_to_server(Users(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
