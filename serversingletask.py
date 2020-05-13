# _*_ coding:utf-8 _*_

#from xmlrpc.server import SimpleXMLRPCServer
#from socketserver import ThreadingMixIn
#import xmlrpc.client
import os
import logging
import time

from http.server import BaseHTTPRequestHandler
from urllib import parse

class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        '''
        parsed_path = parse.urlparse(self.path)
        message_parts = [
            'CLIENT VALUES:',
            'client_address={} ({})'.format(
                self.client_address,
                self.address_string()),
            'command={}'.format(self.command),
            'path={}'.format(self.path),
            'real path={}'.format(parsed_path.path),
            'query={}'.format(parsed_path.query),
            'request_version={}'.format(self.request_version),
            '',
            'SERVER VALUES:',
            'server_version={}'.format(self.server_version),
            'sys_version={}'.format(self.sys_version),
            'protocol_version={}'.format(self.protocol_version),
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append(
                '{}={}'.format(name, value.rstrip())
            )
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        '''
        imagename = '/tmp/ramdisk/phoneimage.jpg'
        cmd = "raspistill -w 2464 -h 3280 -rot 270 -vf -hf -ISO 50 -n -t 50 -o %s" %imagename
        os.system(cmd)
        time.sleep(0.1)

        self.send_response(200)
        self.send_header('Content-Type',
                         'image/jpg')
        self.end_headers()
        with open(imagename, 'rb') as file:
            self.wfile.write(file.read())

if __name__ == '__main__':
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 8080), GetHandler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


'''
class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class RequestHandler():#pyjsonrpc.HttpRequestHandler):
    def __init__(self):
        #self.logger = logging.getLogger('PSILOG')
        pass

    def CloseServer(self):
        server.shutdown()
    
    def capture(self, cam):
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
    #logger = CreateLog()

    server = ThreadXMLRPCServer(('0.0.0.0', 8888), allow_none=True) # 初始化
    handler = RequestHandler()
    server.register_instance(handler)
    print("Listening for Client")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Exiting keyinterrupt")
'''