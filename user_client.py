from __future__ import print_function
import logging

import grpc

import users_pb2
import users_pb2_grpc

import getpass

# This method confirms the password
def password_confirmation(password, confirmation):

     while password != confirmation:
        print("Your passwords don't match, please try again")
        password =  getpass.getpass("Enter a password for your account: ")
        confirmation =  getpass.getpass("Please confirm your password by retyping: ")
        if password == confirmation:
            break
        continue

# This method registers a new user 
def register_user(stub):

    new_username = input("Enter a username for your account: ")

    new_password =  getpass.getpass("Enter a password for your account: ")
    confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
    password_confirmation(new_password, confirm_password)
    
    response = stub.CreateUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))
    
    while response.message == "false":
        new_username = input("The username you have chosen already exists, please choose another username for your account: ")
        new_password =  getpass.getpass("Enter a password for your account:")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

        response = stub.CreateUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))

# This method allows user to login to their account
def user_login(stub):
    # Client takes username and password 
    # Client sends credentials to server via RPC call 
    # Server compares received credentials with locally stored credentials, and replies with authentication token to client if credentials match. The token must be a 
    # random 64 bit string"
    # Server stores authentication token assigned to user and assigns expiry (arbitrary time)
    # Server responds with authentication failure if username does not exist, ​or password is invalid
    print("To be implemented...")

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = users_pb2_grpc.UsersStub(channel)

        # User Menu:
        options_menu = "0"   
        while not options_menu == "q" :
            options_menu = input("If you already have an account then enter 1, enter 2 to Register an Account, or enter 'q' to quit: ")
            if options_menu == "1" :
               user_login(stub)  
            if options_menu == "2" :
                register_user(users_pb2_grpc.UsersStub(channel))
            if options_menu !="q" and options_menu != "1" and options_menu != "2" :
                print("Sorry, your input is invalid, please try again: ")
        quit()

if __name__ == "__main__":
    logging.basicConfig()
    run()