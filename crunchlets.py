import datetime
import errno
import functools
import re
import socket
import time

from tornado import ioloop, iostream

def init_crunch(crunchpool):
    def connection_ready(sock, io_loop, fd, events):
        while True:
            try:
                connection, address = sock.accept()
                stream = iostream.IOStream(connection)
                crunchlet = CrunchLet(io_loop, stream, address)
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
    callback = functools.partial(connection_ready, sock, io_loop)
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
    def __init__(self, io_loop, stream, address):
        self.io_loop = io_loop
        self.stream = stream
        self.address = address
        self.delimiter = '\r\n\r\n'
        self.http_queue = {}
        self.uid = None
        self.timeout = None

    def handle_connection(self):
        self.recv(self.dispatch_commands)
        self.schedule_ping()

    def schedule_ping(self):
        if not self.timeout == None:
            self.io_loop.remove_timeout(self.timeout)

        def send_ping():
            self.send('PING')

        self.timeout = self.io_loop.add_timeout(datetime.timedelta(minutes=2), send_ping)

    def send(self, string, callback=None):
        print '>> ' + string
        self.stream.write(string + self.delimiter, callback)

    def recv(self, callback=None):
        while self.stream.reading() == True:
            continue

        def onread(data):
            data = data.replace(self.delimiter, '')
            print '<< '  + data
            if not callback == None:
                callback(data)

        self.stream.read_until(self.delimiter, onread)

    def send_error(errmsg):
        self.send('ERROR ' + errmsg, self.handle_connection)

    def dispatch_commands(self, received):
        cmd, args = self.parse_command(received)
        if cmd == 'IDENT':
            if len(args) < 2:
                self.send_error('Need arguments to IDENT')
            self.uid = args[0]
            passwd = args[1]
            self.send('ACK', self.handle_connection)

        elif cmd == 'CONTENT':
            if self.uid == None:
                self.send_error('Not authenticated.')
            else:
                ts = args[0]
                content = ' '.join(args[1:])
                self.process_request(ts, content)

        elif cmd == 'PONG':
            self.handle_connection()

    def process_request(self, ts, content):
        if ts in self.http_queue:
            self.http_queue[ts].write_response(content.decode('base64'), 200)

    def parse_command(self, data):
        tokens = data.split(' ')
        return (tokens[0], tokens[1:])

    def fetch(self, resource, http_response):
        def onfetch():
            self.handle_connection()

        ts = str(time.time()).replace('.', '')
        self.http_queue[ts] = http_response
        self.send(
            'FETCH {0} {1}'.format(str(time.time()).replace('.', ''), resource),
            onfetch)