import logging
import time

from gevent import Greenlet
import gevent


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
class Crunchlet(Greenlet):
    def __init__(self, env, stream, address):
        Greenlet.__init__(self)

        self.crunchpool = env['crunchpool']
        self.database = env['database']

        self.stream = stream
        self.address = address
        self.delimiter = '\r\n'
        self.http_queue = {}
        self.uid = None

    def _run(self):
        while True:
            self.read_next_command()
            gevent.sleep(0)

    def disconnect(self):
        if self.stream.closed() == False:
            self.send('DICONNECT')

        self.stream.close()
        self.crunchpool.pop(str(self.address))

    def identify(self, uid, password):
        crunchpool = self.crunchpool
        for address in crunchpool.keys():
            if crunchpool[address].uid == uid and not(
                crunchpool[address] is self):
                crunchpool[address].disconnect()

        if self.database.authenticate(uid, password) == False:
            return False

        return True

    def read_next_command(self):
        if self.stream.closed():
            logging.error('Stream closed while reading command line.')
            return False

        print 'reading command'
        cmd_line = self.stream.read_until(self.delimiter)

        if not cmd_line:
            self.kill()

        print 'finished reading command'
        return self.process_commands(cmd_line)

    def closed(self):
        return self.stream.closed()

    def send(self, string):
        print '>> ' + string
        self.stream.write(string + self.delimiter)

    def on_content(self, args):
        ts = args[0]
        length = args[1]

        if self.uid == None:
                self.send_error('Not authenticated.')
        else:
            if bytes:
                bytes = self.stream.read_bytes(int(length) + len(self.delimiter))
                self.process_request(ts, bytes[:-2])

    def on_ident(self, args):
        if len(args) < 2:
            self.send_error('Need arguments to IDENT')

        self.uid = args[0]
        passwd = args[1]
        if self.identify(self.uid, passwd) == True:
            logging.info('Auth complete. Sending ACK.')
            self.send('ACK')
        else:
            logging.info('Failed authentication.')
            self.send('IDENTFAIILED')

    def send_error(self, errmsg):
        logging.info(errmsg)
        self.send('ERROR ' + errmsg)

    def process_commands(self, data):
        self.idle = False
        tokens = data.replace(self.delimiter, '').split(' ')
        cmd = tokens[0]
        args = tokens[1:]

        if cmd == 'IDENT':
            self.on_ident(args)

        elif cmd == 'CONTENT':
            self.on_content(args)

        elif cmd == 'PONG':
            logging.info('Received PONG.')

        elif cmd == 'FINISH':
            logging.info(args[0])
            self.finish_request(args[0])

        self.idle = True
        return cmd

    def process_request(self, ts, content):
        """Write the streamed data into an HTTP request."""
        if ts in self.http_queue:
            self.http_queue[ts].write_response(content, 200)

    def finish_request(self, ts):
        """Finish streaming response to an HTTP request."""
        if ts in self.http_queue:
            self.http_queue[ts].finish()

    def send_fetch(self, resource, http_response):
        """Fetch content for an HTTP request from serving node."""
        ts = str(time.time()).replace('.', '')
        self.http_queue[ts] = http_response
        logging.info('sending fetch' + resource)
        self.send('FETCH {0} {1}'.format(str(time.time()).replace('.', ''),
            resource))


class CrunchStream(object):
    def __init__(self, socket):
        self.socket = socket
        self.buffer = ''

    def write(self, data):
        self.socket.send(data)

    def push_to_buffer(self, bytes):
        self.buffer += bytes

    def read_until(self, delimiter):
        while True:
            if delimiter in self.buffer:
                ind = self.buffer.index(delimiter)
                ret_val = self.buffer[:ind]
                self.buffer = self.buffer[ind + len(delimiter):]
                return ret_val

            bytes = self.socket.recv(8192)

            if not bytes:
                return None

            self.buffer += bytes

    def closed(self):
        return False

    def read_bytes(self, num_bytes):
        n_bytes = len(self.buffer)
        while True:
            if n_bytes >= num_bytes:
                ret_val = self.buffer[:num_bytes]
                self.buffer = self.buffer[num_bytes:]
                return ret_val

            bytes = self.socket.recv(8192)

            if not bytes:
                return None

            self.buffer += bytes
            n_bytes += len(bytes)
