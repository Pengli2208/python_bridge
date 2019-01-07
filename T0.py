#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
 
# @File  : 
# @Author: Paul Li
# @Date  : 2019/1/3
# @Desc  :
 
import socket
import select
import time 
from multiprocessing import Process, Lock
#import traceback



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
        print("Server started!")

    def ExceptionMsg(self, e):
        print('repr(e):\t', repr(e))
        #print('traceback.print_exc():', traceback.print_exc())
        #print('traceback.format_exc():\n%s' % traceback.format_exc())

    def handlerec(self, sock, lck):
        print('new rec handler', sock)
        while True:
            try:
                str_rev = sock.recv(1024).decode('utf8')
                #host, port = sock.getpeername()
            except Exception as e:
                str_rev = ''
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
                #print('rev:',newstr)
                self.forward(str_rev, sock, lck)

    def getuniqconnection(self, sock):
        host, port = sock.getpeername()
        ret = host.split('.')
        uniqpost = str(65536*(int(ret[2])*256 + int(ret[3])) + port)
        print("uniqpost", uniqpost)
        return uniqpost

    def registerconnection(self, sock, lck, ret0, ret1):
        lck.acquire()
        ret2 = ret1
        if ret2 == 'host':
            self.mapdiction[ret2] = sock
        else:
            uniq = self.getuniqconnection(sock)
            ret2 += uniq
            self.mapdiction[ret2] = sock
        msg = ret0+':'+ret1+':'+ret2
        print('send msg', msg)
        sock.send(msg.encode('utf8'))
        print('add one map:', ret2, ",", self.mapdiction[ret2])
        lck.release()


    def forward(self, msg, sock, lck):
        uniq = ''
        try:
            ret = msg.split(':', 2)
        except Exception as e:
            self.ExceptionMsg(e)
            return
        
        if msg.find('register_server') != -1:
            self.registerconnection(sock, lck, ret[0], ret[1])
        else:
            if ret[1] in self.mapdiction:
                sock = self.mapdiction.get(ret[1], None)
            if sock is not None:
                lck.acquire()
                sock.send(msg.encode('utf8'))
                lck.release()
            else:
                print('not found socket')
        return uniq
        #print('handle one message')


    def acceptaction(self, lck, num):
        host = [self.srvsock]
        print("rev num:", num)
        while True:
            (_, _, _) = select.select(host, [], [])
            try:
                newsock, (_, _) = self.srvsock.accept()
                # 添加连接
                lck.acquire()
                print('new connected', newsock)
                self.descripors.append(newsock)
                lck.release()
                Process(target=self.handlerec, args=(newsock, lck)).start()
            except Exception as e:
                self.ExceptionMsg(e)
                break


    # 运行监听方法
    def run(self):
        lock = Lock()
        self.acceptaction(lock, self.num)
        
 
    # 建立一个新的连接客户机
    def accept_new_connection(self):
        # 接收请求
        newsock, (_, _) = self.srvsock.accept()
        # 添加连接
        print('new connected', newsock)
        self.descripors.append(newsock)
        #newsock.send("You are Connected\r\n".encode('utf8'))
        #str_send = 'Client joined %s:%s' % (remhost, remport)
        #self.broadcast_str(str_send, newsock)
 
    # 广播函数
    def broadcast_str(self, str_send, my_sock):
        # 遍历已有连接
        exceptval = '126C'
        try:
            ret = str_send.split(':', 2)
        except Exception as e:
            self.ExceptionMsg(e)
            return

        if str_send.find('register_server:') != -1:            
            self.mapdiction[ret[1]] = my_sock
            print('add one map:', ret[1], my_sock)
        else:
            sock = None
            if ret[1] in self.mapdiction:
                sock = self.mapdiction.get(ret[1], None)
                if sock is not None:
                    len1 = sock.send(str_send.encode('utf8'))
                    if len1 < len(str_send):
                        print('send error,', str_send)
                    if str_send.find(exceptval) != -1:
                        print('sendmsg:', str_send)
                else:
                    print('not found socket')
            else:
                print('not find target')
            #for sock in self.descripors:
            #    if sock != self.srvsock and sock != my_sock:
            #        sock.send(str_send.encode('utf8'))

if __name__ == '__main__':
    # 实例化监听服务器
    CServer(5555, 30).run()
