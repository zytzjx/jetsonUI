#!/usr/bin/env python</em>
# coding: utf-8
 
#import pyjsonrpc 

from mprpc import RPCClient
'''
from paramiko import SSHClient
from scp import SCPClient

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect('192.168.1.16', username='pi', password='qa', look_for_keys=False)

with SCPClient(ssh.get_transport()) as scp:
    scp.put("/home/pi/Desktop/pyUI/profiles/aaa/top/aaa.jpg", "/home/pi/Desktop/aaa.jpg")
'''
client = RPCClient('127.0.0.1', 8080)
print (client.call('add', 1, 2))
print(client.call('updateProfile',""))
print(client.call('profilepath','/home/pi/Desktop/pyUI/profiles', 'aaa'))
print(client.call('ResultTest',5))
#client.call('Init')
client.call('TakePicture', 0, False)
client.call('TakePicture', 1)
client.call('TakePicture', 2)
client.call('CreateSamplePoint', 0, 150,200)
#client.call('Uninit')
client.call('CloseServer')

'''
http_client = pyjsonrpc.HttpClient(
    url = "http://localhost:8080/jsonrpc"
    #username = "Username",
    #password = "Password"
)

print http_client.updateProfile()
http_client.Init()
# Result: 3
http_client.call("add",1,2)
print http_client.call("TakePicture",0)
http_client.TakePicture(1)
http_client.TakePicture(2)


http_client.Uninit() 
# It is also possible to use the *method* name as *attribute* name.
http_client.add(1, 2)
# Result: 3
 
# Notifications send messages to the server, without response.
http_client.notify("add", 3, 4)
'''