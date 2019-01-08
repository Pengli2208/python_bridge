#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
# @File  : 
# @Author: Paul Li
# @Date  : 2019/1/3
# @Desc  :
 
 
import socket
import traceback

class CClient:
        # 初始化 传入监听端口即可
    def __init__(self, host, port1):
        self.port = port1
        # 配置参数
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port1))
        print("Client started!")
        self.register = "register_server"
        self.testsend1 = "test1 message, what we try max time<120"
        self.total = 0
        self.cnt = 0
        self.descripors = []

    def prepareMsgHead(self, fr, to):
        strsend = str(fr) + ":" + str(to) + ":"
        return strsend

    def ExceptionMsg(self, e):
        print('repr(e):\t', repr(e))
        #print('traceback.print_exc():', traceback.print_exc())
        #print('traceback.format_exc():\n%s' % traceback.format_exc())

    def runtest2(self, id, target):
        self.id = id
        self.target = target
        strsend_final = self.register + ':' + str(self.id) + ":??"
        print('send ', strsend_final)
        self.client.send(strsend_final.encode('utf8'))
        self.descripors = [self.client]
        while True:
            try:
                str_get = self.client.recv(1024).decode('utf8')                      
            except Exception as e:
                self.ExceptionMsg(e)
                break
            try:
                ret = str_get.split(':', 3)
            except Exception as e:
                self.ExceptionMsg(e)
                continue
            if str(ret[1]).find(self.id) == -1:
                if str(ret[0]).find(self.register) != -1:
                    self.id = ret[2]
                    print('id is updated:', self.id)
                else:
                    print('error rev', str_get)
            else:
                if str(ret[0]).find(self.register) != -1:
                    self.id = ret[2]
                    print('id is updated:', self.id)
                else:
                    str_get = ret[1]+":"+ret[0]+":"+ret[2]
                    len1 = self.client.send(str_get.encode('utf8'))
                    if len1 < len(str_get):
                        print('send error,', str_get)


CClient('127.0.0.1', 5555).runtest2('host', '')