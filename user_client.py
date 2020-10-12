from __future__ import print_function
import logging

import grpc

import users_pb2
import users_pb2_grpc
import sys
import getpass

# This method confirms the password

# This method registers a new user 
def register_user(stub):

    new_username = input("Enter a username for your account: ")

    new_password =  getpass.getpass("Enter a password for your account: ")
    confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
    while new_password != confirm_password:
        print("Your passwords don't match, please try again")
        new_password =  getpass.getpass("Enter a password for your account: ")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

    
    response = stub.CreateUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))
    
    while response.success == False:
        new_username = input("The username you have chosen already exists, please choose another username for your account: ")
        new_password =  getpass.getpass("Enter a password for your account:")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

        response = stub.CreateUserAccount(users_pb2.CreateUserRequest(username=new_username, password=new_password, confirmation=confirm_password))

# deletes a user
def delete_user(stub, uname, tok):
    response = stub.DeleteUserAccount(users_pb2.DeleteUserRequest(username=uname,token=tok))
    if response.success:
        print("your account has been removed successfully.")
        menu_select(stub)
    else:
        print("your Account has not been removed.")
        user_selection(stub,uname,tok)

def user_update(stub, token):
    new_password =  getpass.getpass("Enter a new password for your account: ")
    confirm_password =  getpass.getpass("Please confirm your password by retyping: ")
    while new_password != confirm_password:
        print("Your passwords don't match, please try again")
        new_password =  getpass.getpass("Enter a password for your account: ")
        confirm_password =  getpass.getpass("Please confirm your password by retyping: ")

    response = stub.UpdateUserAccount(users_pb2.UpdateUserRequest(password=new_password, token=token))

    if response.code == 200:
        print("Password updated!\nReturning to login...\n")
        user_login(stub)
    elif response.code == 408:
        print("Login timed out...\nReturning to login...\n")
        user_login(stub)
    else:
        print("New password must differ from old password\nReturning to login...\n")
        user_login(stub)



# This method allows user to login to their account
def user_login(stub):
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    response = stub.LoginUserAccount(users_pb2.LoginUserRequest(username=username, password=password))

    while response.success == False:
        username = input("Incorrect username/password combo. Please try again\nEnter your username: ")
        password = getpass.getpass("Enter your password: ")

        response = stub.LoginUserAccount(users_pb2.LoginUserRequest(username=username, password=password))

    token = response.token
    user_selection(stub, username, token)

# menu once the user has logged in
def user_selection(stub, username, token):
    menu_selection = input("You are now logged in.\n1 to Update Password\n2 to Delete Account\n'q' to Quit\n")
    while menu_selection != '1' and menu_selection != '2' and menu_selection != 'q':
        menu_selection = input("Incorrect input.\n1 to Update Password\n2 to Delete Account\n'q' to Quit\n")
    print(menu_selection)
    if menu_selection == 'q':
        print("Goodbye")
        exit()
    elif menu_selection == '1':
        user_update(stub, token)
    else:
        delete_user(stub, username, token)
        print("selection 2")


    # Client sends credentials to server via RPC call 
    # Server compares received credentials with locally stored credentials, and replies with authentication token to client if credentials match. The token must be a 
    # random 64 bit string"
    # Server stores authentication token assigned to user and assigns expiry (arbitrary time)
    # Server responds with authentication failure if username does not exist, ​or password is invalid

def run():
    ip_address = "localhost"
    if(len(sys.argv) > 1):
        ip_address = sys.argv[1]
    with grpc.insecure_channel(ip_address+':10001') as channel:
        stub = users_pb2_grpc.UsersStub(channel)
        menu_select(stub)
        quit()

# the login screen
def menu_select(stub):
    # User Menu:
    options_menu = "0"   
    while options_menu:
        options_menu = input("If you already have an account then enter 1, enter 2 to Register an Account, or enter 'q' to quit: ")
        if options_menu == "1" :
           user_login(stub)  
        if options_menu == "2" :
            register_user(stub)
        if options_menu == "q":
            quit()
        if options_menu !="q" and options_menu != "1" and options_menu != "2" :
            print("Sorry, your input is invalid, please try again: ")
        

if __name__ == "__main__":
    logging.basicConfig()
    run()
