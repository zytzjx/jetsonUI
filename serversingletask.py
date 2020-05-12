# _*_ coding:utf-8 _*_

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import xmlrpc.client
import os
import logging

class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class RequestHandler():#pyjsonrpc.HttpRequestHandler):
    def __init__(self):
        self.logger = logging.getLogger('PSILOG')

    def CloseServer(self):
        server.shutdown()
    
    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -w 2464 -h 3280 -rot 270 -vf -hf -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        os.system(cmd)
        cmd = "/tmp/ramdisk/phoneimage_%d.jpg" % cam
        handle = open(cmd, 'rb')
        return xmlrpc.client.Binary(handle.read())


def CreateLog():
    import logging
    from logging.handlers import RotatingFileHandler

    formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(funcName)s(%(lineno)d) %(message)s')

    logFile = '/tmp/ramdisk/psi.log'
    handler = RotatingFileHandler(logFile, mode='a', maxBytes=1*1024*1024, 
                                    backupCount=500, encoding=None, delay=False)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger('PSILOG')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

if __name__ == '__main__':
    #app = QApplication([])
    logger = CreateLog()

    server = ThreadXMLRPCServer(('0.0.0.0', 8888), allow_none=True) # 初始化
    handler = RequestHandler()
    server.register_instance(handler)
    logger.info("Listening for Client")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.error("Exiting keyinterrupt")
    