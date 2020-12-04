# COMP4000  

## Instructions to run  

1. run `./compile` script
1. `$ python ./user_server.py`
1. `$ python ./user_client.py`

The client can be passed an IP address to allow running on multiple machines. 

`$ python ./user_client.py IPaddresshere`

Otherwise the client will default to local host.

Run genkey.sh to generate the server credentials.
Use 'localhost' as the Common Name when generating the certificates.
# I'm not sure why this is needed. More research needed.
