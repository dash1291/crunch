import errno
import functools
import re
import socket
import time

from tornado import ioloop, iostream

def init_crunch(crunchpool):
    def connection_ready(sock, fd, events):
        while True:
            try:
                connection, address = sock.accept()
                stream = iostream.IOStream(connection)
                crunchlet = CrunchLet(stream, address)
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
IDENT       ->  
            <-  ACK

Content Retrieval
-----------------

                        <-  FETCH timestamp resource
CONTENT timestamp data  -> 

"""
class CrunchLet():
    def __init__(self, stream, address):
        self.stream = stream
        self.address = address
        self.delimiter = '\r\n\r\n'
        self.http_queue = {}

    def handle_connection(self):
        while self.stream.reading() == True:
            continue
        self.stream.read_until(self.delimiter, self.dispatch_commands)

    def send_error(errmsg):
        self.stream.write('ERROR ' + errmsg)

    def dispatch_commands(self, received):
        cmd, args = self.parse_command(received)
        if cmd == 'IDENT':
            if len(args) < 2:
                self.send_error('Need arguments to IDENT')
            uid = args[0]
            passwd = args[1]
            self.send('ACK' + self.delimiter)
        elif cmd == 'CONTENT':
            ts = args[0]
            content = args[1]
            self.process_request(ts, content)
        self.handle_connection()

    def process_request(self, ts, content):
        if ts in self.http_queue:
            http_queue[ts].write_response(content)

    def parse_command(self, data):
        tokens = data.split(' ')
        return (tokens[0], tokens[1:])

    def fetch(self, resource, http_response):
        ts = str(time.time()).replace('.', '')
        self.http_queue[ts] = http_response
        self.stream.write('FETCH ' + str(time.time()).replace('.', '') + (
            resource))