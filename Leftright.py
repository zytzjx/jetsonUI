import TcpClient
from TcpClient import ClientCommand, TaskCommand
import pickle
import threading
import time

class ClientTcpThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.client = TcpClient.SocketClientThread()
        self.client.start()
        self.handlers = {
            TaskCommand.TAKEPICTURE: self.handle_TAKEPICTURE,
            TaskCommand.PROFILENAME: self.handle_PROFILENAME,
            TaskCommand.IMAGE: self.handle_IMAGE,
            TaskCommand.POINTS: self.handle_POINTS,
            TaskCommand.RESULT: self.handle_RESULT,
        }
        self.profilename=""


    def run(self):
        while True:
            self.client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE, ""))
            reply = self.client.reply_q.get(True)
            #print('sct1: ', reply.type, reply.data)
            datacmd = pickle.loads(bytes(reply.data))
            #print(datacmd)
            self.handlers[datacmd.type](datacmd)
            #client.alive.set()


    def handle_TAKEPICTURE(self,datacmd):
        filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
        with picamera.PiCamera() as camera:
            camera.start_preview()
            camera.capture(self.filepath)
            camera.stop_preview()   

    def handle_PROFILENAME(self,datacmd):
        profilename = datacmd.data

    def handle_IMAGE(self,datacmd):
        filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
        with open(filepath, "rb") as image:
            f = image.read()
            b = bytearray(f)
            self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, TaskCommand(TaskCommand.IMAGE, b)))
            reply = self.client.reply_q.get(True)

    def handle_POINTS(self,datacmd):
        pins = datacmd.data

    def handle_RESULT(self,datacmd):
        self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, TaskCommand(TaskCommand.IMAGE, b)))
        reply = self.client.reply_q.get(True)

    def Connect(self, ip, port):
        self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, (ip, port)))
        return self.client.reply_q.get()

    def disConnect(self):
        self.client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
        return client.reply_q.get()


aaa = ClientTcpThread()
aaa.Connect('10.1.1.183', 5007)
time.sleep(1)
aaa.start()



"""
client = TcpClient.SocketClientThread()
client.start()
client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, ('10.1.1.183', 5007)))
reply = client.reply_q.get(True)
handlers = {
    TaskCommand.TAKEPICTURE: handle_TAKEPICTURE,
    TaskCommand.PROFILENAME: handle_PROFILENAME,
    TaskCommand.IMAGE: handle_IMAGE,
    TaskCommand.POINTS: handle_POINTS,
    TaskCommand.RESULT: handle_RESULT,
}

while True:
    client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE, ""))
    reply = client.reply_q.get(True)
    #print('sct1: ', reply.type, reply.data)
    datacmd = pickle.loads(bytes(reply.data))
    #print(datacmd)
    handlers[datacmd.type](datacmd)
    #client.alive.set()


client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
reply = client.reply_q.get(True)
#print('sct2 close: ', reply.type, reply.data)
"""