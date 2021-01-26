# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" socket class with adapted methods and error trapping, derived from QObject to support Signals
"""

import select
import socket

from PyQt5.QtCore import QObject


class DepthmapNetSocket(QObject):
    def __init__(self, s=None):
        QObject.__init__(self)
        if s is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = s

    def connectSocket(self, host, port):
        msg = ''
        try:
            self.sock.connect((host, port))
        except socket.error as errormsg:
            msg = errormsg.strerror
        return msg

    def sendData(self, data):
        size = len(data)
        totalsent = 0
        try:
            while totalsent < size:
                sent = self.sock.send(data[totalsent:].encode('ascii'))
                if not sent:
                    raise IOError("Socket connection broken")
                totalsent = totalsent + sent
            sent = True
            msg = totalsent
        except socket.error as errormsg:
            # self.closeSocket()
            sent = False
            msg = errormsg
        return sent, str(msg)

    def isReady(self):
        try:
            to_read, to_write, exception = select.select([self.sock], [], [self.sock], 0)
            if exception:
                waiting = False
            else:
                waiting = True
        except:
            waiting = False
        return waiting

    def checkData(self, buff=1):
        try:
            msg = self.sock.recv(buff).decode('ascii')
            if msg == '':
                check = False
            else:
                check = True
        except socket.error as errormsg:
            msg = errormsg
            check = False
        return check, msg

    def dumpData(self, buff=1):
        msg = ''
        try:
            while True:
                chunk = self.sock.recv(buff).decode('ascii')
                if not chunk:
                    break
                msg += chunk
            dump = True
        except socket.error as errormsg:
            msg = errormsg
            dump = False
        return dump, msg

    def receiveData(self, buff=1024, suffix=''):
        msg = ''
        try:
            while True:
                chunk = self.sock.recv(buff).decode('ascii')
                if not chunk:
                    break
                msg += chunk
                if msg.endswith(suffix):
                    break
            receive = True
        except socket.error as errormsg:
            msg = errormsg
            receive = False
        return receive, msg

    def closeSocket(self):
        self.sock.close()
        # self.sock = None
