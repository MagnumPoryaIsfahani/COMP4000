from __future__ import print_function

import getpass
import logging
import sys
import grpc
from fuse import FUSE, FuseOSError, Operations

import users_pb2
import users_pb2_grpc
from passthrough import Passthrough

REMOTE_DIRECTORY = "/home/student/fuse"

# This method registers a new user 
def registerUser(stub):
    while True:
        # input username
        new_username = input("\nEnter a username for your account: ")
        
        # input password
        new_password = getpass.getpass("Enter a password for your account: ")
        confirm_password = getpass.getpass("Please confirm your password by retyping: ")
        if new_password != confirm_password:
            print("\nError: your passwords didn't match.")
            continue

        # send request
        response = stub.createUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))
        
        if not response.success: 
            print("\nError: the username you have chosen already exists, please choose a different one.")
            continue

        print("\nSuccessfully created account for user", new_username)

        return
            

# Deletes a user
# Returns true if success
def deleteUser(stub, uname, tok):
    response = stub.deleteUserAccount(users_pb2.DeleteUserRequest(username=uname,token=tok))
    
    if response.success:
        print("\nYour account has been removed successfully.")
    else:
        print("\nError: your account has not been removed.")

def updateUser(stub, username, token):
    while True:
        new_password =  getpass.getpass("Enter a new password for your account: ")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
        
        if new_password != confirm_password:
            print("\nError: your passwords don't match, please try again")
            continue

        response = stub.updateUserAccount(users_pb2.UpdateUserRequest(password=new_password, token=token, username=username))

        if response.code == grpc.StatusCode.OK.value[0]:
            print("\nPassword updated!")
        elif response.code == grpc.StatusCode.UNAUTHENTICATED.value[0]:
            print("\nError: unauthorized. Token is invalid.")
        elif response.code == grpc.StatusCode.ALREADY_EXISTS.value[0]:
            print("\nError: new password must differ from old password.")
            continue
        elif response.code == grpc.StatusCode.DEADLINE_EXCEEDED.value[0]:
            print("\nError: login timed out...")
        elif response.code == grpc.StatusCode.NOT_FOUND.value[0]:
            print("\nError: database not found.")
        else:
            print("Unknown Error.")
        
        # return to userSelection
        return

# menu once the user has logged in
def userSelection(stub, username, token):
    while True:
        operation = input("""
- YOU ARE LOGGED IN -
    [1] Update Password
    [2] Delete Account
    [3] Mount remote filesystem
    [q] Logout

Please choose an operation: """)
        if operation == '1':
            updateUser(stub, username, token)
        elif operation == '2':
            deleteUser(stub, username, token)
        elif operation == '3':
            # display file structure
            print('\n- FILE STRUCTURE -')
            reply = stub.displayTree(users_pb2.DisplayTreeRequest())
            print(reply.tree)
            
            # input mountpoint
            mountpoint = input('Enter the mountpoint: ')
            print("[ctrl+c] to unmount...")
            
            # mount remote fs
            FUSE(Passthrough(REMOTE_DIRECTORY, stub), mountpoint, nothreads=True, foreground=True)
            print('\nFilesystem was unmounted...\n')
            continue
        elif operation != 'q':
            print('Error: invalid input.')
            continue

        # logout of account
        print("\nLogging out...")
        return

# Client sends credentials to server via RPC call 
# Server compares received credentials with locally stored credentials, and replies with authentication token to client if credentials match. The token must be a 
# random 64 bit string"
# Server stores authentication token assigned to user and assigns expiry (arbitrary time)
# Server responds with authentication failure if username does not exist, ​or password is invalid
# the login screen
def menuSelect(stub):
    # User Menu:
    while True:
        operation = input("""
- WELCOME TO THE COMP4000 REMOTE FILESYSTEM -
    [1] Login to an existing account
    [2] Register an account 
    [q] Quit
    
Please choose an operation: """)
        if operation == "1" :
            username = input("Enter your username: ")
            password = getpass.getpass("Enter your password: ")
            response = stub.loginUserAccount(users_pb2.LoginUserRequest(username=username, password=password))
            if response.success:
                userSelection(stub, username, response.token)
            else:
                print('Error: incorrect username/password combo.')
            
        elif operation == "2" :
            registerUser(stub)
        elif operation == "q":
            quit()
        else:
            print("Error: invalid input.")

def run():
    ip_address = "localhost"
    if(len(sys.argv) > 1):
        ip_address = sys.argv[1]
    with open('server.crt','rb') as f:
        creds = grpc.ssl_channel_credentials(root_certificates=f.read())
    #with grpc.insecure_channel(ip_address+':10001') as channel:
    with grpc.secure_channel(ip_address+':10002', creds) as channel:
        stub = users_pb2_grpc.UsersStub(channel)
        menuSelect(stub)
        quit()

if __name__ == "__main__":
    logging.basicConfig()
    run()
