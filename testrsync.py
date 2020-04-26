#!/usr/bin/env python3
#coding: utf-8

import os
import time
import traceback
import pexpect
import myconstdef

#按照这个格式填写目的IP和密码
SERVERS = {
    "192.168.1.12":"qa",
}

source_path = '/tmp/ramdisk'
destination_ip = myconstdef.IP
destination_path = '/tmp/ramdisk/'
rsync_cmd = 'rsync -avzP --delete pi@%s:%s %s' % (destination_ip, destination_path, source_path)

def rsync():
    t = time.strftime('%Y:%m:%d_%H:%M:%S',time.localtime(time.time()))
    try:
        child = pexpect.spawn(rsync_cmd)
        index = child.expect(['password:','continue connecting (yes/no)?',pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            print (rsync_cmd)
            try:
                child.sendline("qa")#SERVERS[destination_ip])
                child.expect(pexpect.EOF)
                m = "".join([t," ",rsync_cmd," ","OK"])
                print(m)
                print (child.before)
            except Exception as e:
                m = "".join([t," ",rsync_cmd," ","ERROR"])
                print(m)
                print (str(e))
        elif index == 1:
            print (rsync_cmd)
            try:
                child.sendline('yes')
                child.expect(['password:'])
                child.sendline(SERVERS[destination_ip])
                child.expect(pexpect.EOF)
                m = "".join([t," ",rsync_cmd," ","OK"])
                print(m)
                print (child.before)
            except Exception as e:
                m = "".join([t," ",rsync_cmd," ","ERROR"])
                print(m)
                print (str(e))
        '''elif index == 2:
            m = "".join([t," ",rsync_cmd," ","ERROR"])
            print(m)
            print ("子程序异常，退出!")
        elif index == 3:
            m = "".join([t," ",rsync_cmd," ","TIMEOUT"])
            print(m)
            print ("连接超时")'''
    except:
        traceback.print_exc()
'''
if __name__ == '__main__':
    print ("输入正确执行中...")
    rsync(rsync_cmd)

'''
