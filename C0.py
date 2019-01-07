#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
 
# @File  : 
# @Author: Paul Li
# @Date  : 2019/1/3
# @Desc  :
 
 
import socket
import select
import time 
import traceback
from multiprocessing import Process, Lock

class CClient:
        # 初始化 传入监听端口即可
    def __init__(self, host, port1):
        self.port = port1
        # 配置参数
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port1))
        print("Client started!")
        self.testsend1 = "test1 message, what we try max time<120"
        self.time_start = time.time()
        self.time_end = time.time()
        self.total = 0
        self.cnt = 1        
        self.register = "register_server"
        self.descripors =[]
    # 运行监听方法
    def prepareMsgHead(self, fr, to):
        strsend = str(fr) + ":" + str(to) + ":"
        return strsend
    def ExceptionMsg(self, e):
        print('repr(e):\t', repr(e))
        #print('traceback.print_exc():', traceback.print_exc())
        #print('traceback.format_exc():\n%s' % traceback.format_exc())

    def revHandle(self, strsend, cntavg):
        try:
            str_get = self.client.recv(1024).decode('utf8')                                
        except Exception as e:
            self.ExceptionMsg(e)
            return

        self.time_end = time.time()
        t1 = (self.time_end-self.time_start)*1000
        self.total = self.total + t1
        #print('rev:', str_get)
        if self.cnt % cntavg == 1:
            print(str(self.cnt), 'time cost', self.total/self.cnt, 'ms')

        if str(str_get).find(strsend) == -1:
            try:
                ret = str_get.split(':', 2)
                print('ret0:', ret[0])
                if str(ret[0]).find(self.register) != -1:
                    self.id = ret[2]
                    print('id is updated:', self.id)
                else:
                    print('error rev', str_get)
            except Exception as e:
                self.ExceptionMsg(e)
                return

    def runtest1(self, id, target, cntavg):
        self.id = id
        self.target = target
        strsend_final = self.register + ':'+str(self.id) + ":??"
        self.time_start = time.time()
        self.client.send(strsend_final.encode('utf8'))
        self.descripors = [self.client]
        self.revHandle(strsend_final, cntavg)

        time.sleep(1)
        while True:
            # 获取 新的连接申请
            self.cnt += 1
            strsend = self.testsend1 + "->" + str(self.cnt)
            self.time_start = time.time()
            strsend_final = self.prepareMsgHead(self.id, self.target) + strsend
            #print('send:', strsend_final)
            len1 = self.client.send(strsend_final.encode('utf8'))
            if len1 < len(strsend_final):
                print('send error,', strsend_final)  
            self.revHandle(strsend, cntavg)            
            time.sleep(0.05)

if __name__ == '__main__':
    for i in range(10):
        Process(target=CClient('127.0.0.1', 5555).runtest1, args=('0', 'host', 40)).start()
 #   CClient('127.0.0.1', 5555).runtest1('0', 'host')
