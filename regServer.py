#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
 
# @File  : 
# @Author: Paul Li
# @Date  : 2019/1/3
# @Desc  :
 
import socket
import select
import base64
import time
import os
from multiprocessing import Process, Lock

import traceback




# 创建一个类
class CServer:
    # 初始化 传入监听端口即可
    def __init__(self, port, num):
        if num < 10:
            num = 10
        self.port = port
        self.num = num        # 配置参数
        self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srvsock.bind(("", port))
        self.srvsock.listen(num)  # 设置监听数量
        # 添加在线服务器
        self.descripors = [self.srvsock]
        self.mapdiction = {}
        self.uniqpost = ''
        self.processlist = []
        self.printf("Server started!")

    def printf(self, *args):
        print(time.strftime("%Y-%m-%d %H-%M-%S"), *args)


    def ExceptionMsg(self, e):
        print('repr(e):\t', repr(e))
        print('traceback.print_exc():', traceback.print_exc())
        print('traceback.format_exc():\n%s' % traceback.format_exc())

    def handlerec(self, sock, lck):
        self.printf('new rec handler', sock)
        while True:
            try:
                str_rev = sock.recv(1024).decode('utf8')
                #host, port = sock.getpeername()
            except Exception as e:
                str_rev = ''
                self.printf("rev exception")
                self.ExceptionMsg(e)
                pass
            # 检测是否断开连接
            
            if str_rev == '':
                #str_send = 'Client left %s:%s\r\n' % (host, port)
                #self.broadcast_str(str_send, sock)
                #sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
                sock.close
                lck.acquire()
                self.descripors.remove(sock)
                lck.release()
                break
            else:
                #newstr = '[%s:%s] %s' % (host, port, str_rev)
                self.printf('rev: ',str_rev)
                self.forward(str_rev, sock, lck)

    def getuniqconnection(self, sock):
        host, port = sock.getpeername()
        ret = host.split('.')
        uniqpost = str(65536*(int(ret[2])*256 + int(ret[3])) + port)
        self.printf("uniqpost", uniqpost)
        return uniqpost

    def registerconnection(self, sock, lck, ret0, ret1):
        lck.acquire()
        
        filename = os.path.join(os.getcwd(), "register.txt")
        fo = open(filename,'a+')
        ret2 = ret1
        if ret2 == 'host':
            self.mapdiction[ret2] = sock
        else:
            keys = bytes(ret2, encoding='utf8') 
            pc = base64.encodebytes(keys)  # 初始化密钥
            pc1 = base64.b64decode(pc)
            pc1 = pc1.decode(encoding='utf-8', errors='strict')
            pc = pc.decode(encoding='utf-8', errors='strict')
            self.printf("reg:", ret2, " code:", pc, " decode:",pc1)
            fo.write("time," + time.strftime("%Y-%m-%d %H-%M-%S")+"\r\n")
            fo.write('socket, '+ str(socket)+"\r\n")
            fo.write("reg," + ret2 +",code," + str(pc) +",decode," +str(pc1)+"\r\n")
            self.mapdiction[ret2] = sock
            msg = ret0+':'+pc+':'+ pc
            self.printf('send msg, ', msg)
            fo.write('send msg,'+msg +"\r\n")
            sock.send(msg.encode('utf8'))
            self.printf('add one map:', ret2, ",", self.mapdiction[ret2])
        
        fo.close()
        lck.release()

    def forward(self, msg, sock, lck):
        uniq = ''
        try:
            ret = msg.split(':', 2)
        except Exception as e:
            self.printf("forward exception")
            self.ExceptionMsg(e)
            return
        
        if msg.find('register_') != -1:
            self.registerconnection(sock, lck, ret[0], ret[1])
        else:
            if ret[1] in self.mapdiction:
                sock = self.mapdiction.get(ret[1], None)
            if sock is not None:
                lck.acquire()
                sock.send(msg.encode('utf8'))
                lck.release()
            else:
                self.printf('not found socket')        
        #print('handle one message')
        return uniq

    def acceptaction(self, lck, num):
        host = [self.srvsock]
        self.printf("rev num:", num)
        while True:
            (_, _, _) = select.select(host, [], [])
            try:
                newsock, (_, _) = self.srvsock.accept()
                # 添加连接
                lck.acquire()
                self.printf('new connected', newsock)
                self.descripors.append(newsock)                
                process1 = Process(target=self.handlerec, args=(newsock, lck))
                self.processlist.append(process1)
                lck.release()
                process1.start()
            except Exception as e:
                
                self.printf("acceptaction exception")
                self.ExceptionMsg(e)
                break

    def run(self):
        lock = Lock()
        self.acceptaction(lock, self.num)
        for inst in self.processlist:
            inst.join()


if __name__ == '__main__':
    # 实例化监听服务器
    CServer(5555, 30).run()
