#!/usr/bin/env python
# encoding: utf-8

#use nc -u 127.0.0.1 8888 to communicate with the server 1-way
"""A non-blocking, single-threaded TCP server."""
from __future__ import absolute_import, division, print_function, with_statement

import errno
import os
import socket
import ssl
import stat
import sys

from tornado.log import app_log
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream, SSLIOStream
from tornado.netutil import ssl_wrap_socket
from tornado import process
#from tornado.netutil import set_close_exec

#web socket support
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.websocket
import tornado.options

PIPE = None

class UDPServer(object):
    def __init__(self, io_loop=None):
        self.io_loop = io_loop
        self._sockets = {}  # fd -> socket object
        self._pending_sockets = []
        self._started = False

    def add_sockets(self, sockets):
        if self.io_loop is None:
            self.io_loop = IOLoop.instance()

        for sock in sockets:
            self._sockets[sock.fileno()] = sock
            add_accept_handler(sock, self._on_recive,
                               io_loop=self.io_loop)

    def bind(self, port, address=None, family=socket.AF_UNSPEC, backlog=25):
        sockets = bind_sockets(port, address=address, family=family,
                               backlog=backlog)
        if self._started:
            self.add_sockets(sockets)
        else:
            self._pending_sockets.extend(sockets)

    def start(self, num_processes=1):
        assert not self._started
        self._started = True
        if num_processes != 1:
            process.fork_processes(num_processes)
        sockets = self._pending_sockets
        self._pending_sockets = []
        self.add_sockets(sockets)

    def stop(self):
        for fd, sock in self._sockets.iteritems():
            self.io_loop.remove_handler(fd)
            sock.close()

    def _on_recive(self, data, address):
        print(data)
        host = address[0]
        port = address[1]
        print(host)
        print(port)
        if(PIPE):
             PIPE.write_message(data)
	#sock = socket.socket(
        #socket.AF_INET, socket.SOCK_STREAM)
        #sock.connect((host, port))
        #sock.send("abcde\r\n\r\n")

def bind_sockets(port, address=None, family=socket.AF_UNSPEC, backlog=25):
    sockets = []
    if address == "":
        address = None
    flags = socket.AI_PASSIVE
    if hasattr(socket, "AI_ADDRCONFIG"):
        flags |= socket.AI_ADDRCONFIG
    for res in set(socket.getaddrinfo(address, port, family, socket.SOCK_DGRAM,
                                      0, flags)):
        af, socktype, proto, canonname, sockaddr = res
        sock = socket.socket(af, socktype, proto)
        #set_close_exec(sock.fileno())
        if os.name != 'nt':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if af == socket.AF_INET6:
            if hasattr(socket, "IPPROTO_IPV6"):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(0)
        sock.bind(sockaddr)
        sockets.append(sock)
    return sockets

if hasattr(socket, 'AF_UNIX'):
    def bind_unix_socket(file, mode=0o0600, backlog=128):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        #set_close_exec(sock.fileno())
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        try:
            st = os.stat(file)
        except (OSError) as err:
            if err.errno != errno.ENOENT:
                raise
            else:
                if st.S_ISSOCK(st.st_mode):
                    os.remove(file)
                else:
                    raise ValueError("File %s exists and is not a socket", file)
        sock.bind(file)
        os.chmod(file, mode)
        sock.listen(backlog)
        return sock

def add_accept_handler(sock, callback, io_loop=None):
    if io_loop is None:
        io_loop = IOLoop.instance()

    def accept_handler(fd, events):
        while True:
            try:
                data, address = sock.recvfrom(2500)
            except (socket.error) as e:
                if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise
            callback(data, address)
    io_loop.add_handler(sock.fileno(), accept_handler, IOLoop.READ)


LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
        global PIPE
        PIPE = self
    
    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")
        global PIPE
        PIPE = None

    def check_origin(self, origin):
        """
        Override the origin check if needed
        """
        return True

class ChannelHandler(tornado.websocket.WebSocketHandler):
    """
    Handler that handles a websocket channel
    """
    @classmethod
    def urls(cls):
        return [
            (r'/web-socket/', cls, {}),  # Route/Handler/kwargs
        ]
    
    def initialize(self):
        self.channel = None
    
    def open(self, channel):
        """
        Client opens a websocket
        """
        self.channel = channel
    
    def on_message(self, message):
        """
        Message received on channel
        """
        print("Received",message)
    
    def on_close(self):
        """
        Channel is closed
        """
    
    def check_origin(self, origin):
        """
        Override the origin check if needed
        """
        return True







server = UDPServer()
server.bind(8888)
server.start(1)
print("Start UDP Server on Port:8888")

app = tornado.web.Application([
            (r'/web-socket/', EchoWebSocket, {}),  # Route/Handler/kwargs
        ])#ChannelHandler.urls())
    
# Setup HTTP Server
http_server = tornado.httpserver.HTTPServer(app)
http_server.listen(8013)
print("Start websocket server on port 8013")
IOLoop.instance().start()
