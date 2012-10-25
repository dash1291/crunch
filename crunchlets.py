import errno
import functools
import re
import socket
import time

from tornado import ioloop

def init_crunch(crunchpool):
    def connection_ready(sock, fd, events):
        while True:
            try:
                connection, address = sock.accept()
                crunchlet = CrunchLet(connection, address)
                crunchpool[str(address)] = crunchlet
            except socket.error, e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                return
            connection.setblocking(0)
            crunchlet.handle_connection()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(("", 8890))
    sock.listen(128)

    io_loop = ioloop.IOLoop.instance()
    callback = functools.partial(connection_ready, sock)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    io_loop.start()


"""
Crunch Protocol

Handshake
---------

Client          Server
Connection  ->  
            <-  INIT
IDENT       ->  ACK

"""

class CrunchLet():
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.delimiter = '\r\n\r\n'

    def handle_connection(self):
        conn = self.connection
        while 1:
            try:
                recv_buffer = conn.recv(256)
                received = received + recv_buffer
                if self.delimiter in str(received):
                    self.dispatch_commands(received)
                    received = ''
            except:
                continue
            recv_buffer = ''

    def send(self, string):
        sent = False
        while not sent:
            try:
                self.connection.send(string)
                sent = True
            except:
                continue

    def recv(self):
        received = ''
        while True:
            try:
                received = received + conn.recv(256)
                if self.delimiter in received:
                    return received.replace(self.delimiter, '')
            except:
                continue

    def send_error(errmsg):

        try:
            self.connection.send('ERROR ' + errmsg)
        except:


    def dispatch_commands(self, received):
        cmd, args = self.parse_command(received)

        print cmd
        if cmd == 'IDENT':
            if len(args) < 2:
                self.send_error('Need arguments to IDENT')
            uid = args[0]
            passwd = args[1]
            self.connection.send('ACK' + self.delimiter)

    def parse_command(self, data):
        tokens = data.split(' ')
        return (tokens[0], tokens[1:])