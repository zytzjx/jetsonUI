import socket 
from threading  import Thread , RLock
#from socketserver import ThreadingMixIn
import struct
#import error as SocketError
import errno
import logging
from queue import Queue
from TcpClient import TaskCommand,ClientCommand,ClientReply
import pickle
import time
from io import BytesIO

# Multithreaded Python server : TCP Server Socket Thread Pool

class ClientThread(Thread): 
    def __init__(self,ip,port,conn, reply_q=None):
        Thread.__init__(self)
        self.ip = ip 
        self.port = port 
        self.conn = conn
        self.peername=socket.getfqdn(ip)
        print ("[+] New server socket thread started for " + ip +":" + str(port) )
        self.reply_q = reply_q or Queue()

    def SendDataToClient(self, data):
        realdata=data.DataBytes()
        header = struct.pack('<L', len(realdata))
        try:
            self.conn.sendall(header + realdata)
        except IOError as e:
            logging.debug(str(e))
            logging.info("A")
            self.reply_q.put(self._error_reply(str(e)))

    def _recv_n_bytes(self, n):
        """ Convenience method for receiving exactly n bytes from
            self.conn (assuming it's open and connected).
        """
        #data = ''
        bytIO = BytesIO()
        while bytIO.getbuffer().nbytes < n:
            chunk = self.conn.recv(n - bytIO.getbuffer().nbytes)
            if chunk == '':
                break
            #data += chunk
            bytIO.write(chunk)
        return bytIO.getvalue()

    def _error_reply(self, errstr):
        logging.info("0"+errstr)
        return ClientReply(ClientReply.ERROR, errstr)

    def _success_reply(self, data=None):
        return ClientReply(ClientReply.SUCCESS, data)

    def run(self): 
        running = True
        while running : 
            try:
                header_data = self._recv_n_bytes(4)
                if len(header_data) == 4:
                    msg_len = struct.unpack('<L', bytes(header_data))[0]
                    data = self._recv_n_bytes(msg_len)
                    if len(data) == msg_len:
                        self.reply_q.put(self._success_reply(pickle.loads(data)))
                        continue
                running = False
                print("exit thread??")
                self.reply_q.put(self._error_reply('Socket closed prematurely'))
            except IOError as e:
                if e.errno == errno.ECONNRESET:
                    print("Socket client close.\n")

                self.conn.close()
                self.reply_q.put(self._error_reply(str(e)))
                print("except thread")
                running=False

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0' 
TCP_PORT = 5007 
BUFFER_SIZE = 1024 # Usually 1024, but we need quick response 
threads = [] 
r = RLock()

def _StartTcpServer(nport=TCP_PORT):
    TCP_PORT = nport
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    tcpServer.bind((TCP_IP, TCP_PORT)) 
    global threads

    while True: 
        tcpServer.listen(4) 
        print ("Multithreaded Python server : Waiting for connections from TCP clients..." )
        
        (conn, (ip,port)) = tcpServer.accept() 
        newthread = ClientThread(ip,port, conn) 
        newthread.start() 
        r.acquire()
        threads.append(newthread) 

        print(threads)
        threads = [item for item in threads if item.is_alive()]
        r.release()

    #for t in threads: 
    #    t.join()


def startThreadServer():
    Thread(target=_StartTcpServer).start()

def TakePicture():
    global threads
    r.acquire()
    for t in threads:
        t.SendDataToClient(TaskCommand(TaskCommand.TAKEPICTURE, "take picture"))
    r.release()

def SendProfile(profile):
    global threads
    r.acquire()
    for t in threads:
        t.SendDataToClient(TaskCommand(TaskCommand.PROFILENAME, profile))
    r.release()

def GetImage():
    global threads
    r.acquire()
    data=TaskCommand(TaskCommand.IMAGE, "imagefile")
    for t in threads:
        t.SendDataToClient(data)
    r.release()

def PrintImage():
    global threads
    r.acquire()
    for t in threads:
        if t.reply_q.empty():
            continue
        reply = t.reply_q.get(True,0.2)
        if reply!=None and reply.type!=ClientReply.ERROR:
            print(str(reply.data.type)+str(len(reply.data.data)))
    r.release()

def GetResult():
    global threads
    r.acquire()
    for t in threads:
        t.SendDataToClient(TaskCommand(TaskCommand.RESULT,"result"))
    r.release()

