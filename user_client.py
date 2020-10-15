from __future__ import print_function
import logging

import grpc

import users_pb2
import users_pb2_grpc
import sys
import getpass

# This method confirms the password

# This method registers a new user 
def registerUser(stub):

    new_username = input("Enter a username for your account: ")

    new_password =  getpass.getpass("Enter a password for your account: ")
    confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
    while new_password != confirm_password:
        print("Your passwords don't match, please try again")
        new_password =  getpass.getpass("Enter a password for your account: ")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

    
    response = stub.createUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))
    
    while response.success == False:
        new_username = input("The username you have chosen already exists, please choose another username for your account: ")
        new_password =  getpass.getpass("Enter a password for your account:")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

        response = stub.createUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))

# deletes a user
def deleteUser(stub, uname, tok):
    response = stub.deleteUserAccount(users_pb2.DeleteUserRequest(username=uname,token=tok))
    if response.success:
        print("your account has been removed successfully.")
        menuSelect(stub)
    else:
        print("your Account has not been removed.")
        userSelection(stub,uname,tok)

def userUpdate(stub, token):
    new_password =  getpass.getpass("Enter a new password for your account: ")
    confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
    
    while new_password != confirm_password:
        print("Your passwords don't match, please try again")
        new_password =  getpass.getpass("Enter a password for your account: ")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

    response = stub.updateUserAccount(users_pb2.UpdateUserRequest(password=new_password, token=token))

    if response.code == 200:
        print("Password updated!\nReturning to login...\n")
        userLogin(stub)
    elif response.code == 401:
        print("Error, unauthorized. Token is invalid.\nReturning to login...\n")
        userLogin(stub)
    elif response.code == 405:
        print("New password must differ from old password.\nReturning to login...\n")
        userLogin(stub)
    elif response.code == 408:
        print("Login timed out...\nReturning to login...\n")
        userLogin(stub)
    elif response.code == 404:
        print("Error, Database not found.\nReturning to login...\n")
        userLogin(stub)
    else:
        print("Unknown Error.\nReturning to login...\n")
        userLogin(stub)

# This method allows user to login to their account
def userLogin(stub):
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    response = stub.loginUserAccount(users_pb2.LoginUserRequest(username=username, password=password))

    while response.success == False:
        username = input("Incorrect username/password combo. Please try again\nEnter your username: ")
        password = getpass.getpass("Enter your password: ")

        response = stub.loginUserAccount(users_pb2.LoginUserRequest(username=username, password=password))

    token = response.token
    userSelection(stub, username, token)

# menu once the user has logged in
def userSelection(stub, username, token):
    menuSelection = input("You are now logged in.\n1 to Update Password\n2 to Delete Account\n'q' to Quit\n")
    while menuSelection != '1' and menuSelection != '2' and menuSelection != 'q':
        menuSelection = input("Incorrect input.\n1 to Update Password\n2 to Delete Account\n'q' to Quit\n")
    print(menuSelection)
    if menuSelection == 'q':
        print("Goodbye")
        exit()
    elif menuSelection == '1':
        userUpdate(stub, token)
    else:
        deleteUser(stub, username, token)

    # Client sends credentials to server via RPC call 
    # Server compares received credentials with locally stored credentials, and replies with authentication token to client if credentials match. The token must be a 
    # random 64 bit string"
    # Server stores authentication token assigned to user and assigns expiry (arbitrary time)
    # Server responds with authentication failure if username does not exist, ​or password is invalid
# the login screen
def menuSelect(stub):
    # User Menu:
    options_menu = "0"   
    while options_menu:
        options_menu = input("If you already have an account then enter 1, enter 2 to Register an Account, or enter 'q' to quit: ")
        if options_menu == "1" :
           userLogin(stub)  
        if options_menu == "2" :
            registerUser(stub)
        if options_menu == "q":
            quit()
        if options_menu !="q" and options_menu != "1" and options_menu != "2" :
            print("Sorry, your input is invalid, please try again: ")

def run():
    ip_address = "localhost"
    if(len(sys.argv) > 1):
        ip_address = sys.argv[1]
    with grpc.insecure_channel(ip_address+':10001') as channel:
        stub = users_pb2_grpc.UsersStub(channel)
        menuSelect(stub)
        quit()
        

if __name__ == "__main__":
    logging.basicConfig()
    run()
