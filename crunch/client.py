import logging

from gevent import Greenlet, socket
import gevent


logging.basicConfig(level=logging.DEBUG)

delimiter = '\r\n'
stream = None
config = None
request_pool = []
io_loop = None


class RequestConveyor(Greenlet):
    """Thread that does rotation of requests in the request pool.

    Response for each request is written to the stream one piece (i.e. of
    length given by STREAM_LENGTH) at a time."""

    def __init__(self, stream, request_pool, stream_length=8192):
        Greenlet.__init__(self)
        self.request_pool = request_pool
        self.stream = stream
        self.stream_length = stream_length

    def _run(self):
        STREAM_LENGTH = self.stream_length

        while True:
            for request in self.request_pool:
                finished = False
                ts = request['ts']
                response_content = request['response']
                # write data into the stream one piece at a time
                if len(response_content) >= STREAM_LENGTH:
                    resp_stream = response_content[:STREAM_LENGTH]
                    response_content = response_content[STREAM_LENGTH:]
                else:
                    resp_stream = response_content
                    response_content = ''
                    self.request_pool.remove(request)
                    finished = True

                request['response'] = response_content
                response = 'CONTENT {0} {1}{2}{3}'.format(
                    ts, len(resp_stream), delimiter, resp_stream)
                send_data(response)
                print 'sent'
                #callback = functools.partial(send_data, response)
                #globals()['io_loop'].add_callback(callback)


                if finished == True:
                    fin = 'FINISH {0}'.format(ts)
                    #callback = functools.partial(send_data, fin)
                    print 'finishing'
                    #globals()['io_loop'].add_callback(callback)
                    send_data(fin)

            gevent.sleep(0)

    def stop(self):
        self.quit = True


def build_headers(headers, status_code=200):
    if status_code == 200:
        status = '200 OK'
    elif status_code == 404:
        status = '404 NOT FOUND'
    else:
        status = '200 OK'

    header_string = 'HTTP/1.1 {0}\r\n'.format(status)
    for key in headers.keys():
        header_string = header_string + (
            '{0}: {1}\r\n'.format(key, headers[key]))

    return header_string


def send_data(content):
    return stream.write(content + delimiter)

def on_unrecognized(cmd):
    logging.info('Unrecognized command. %s' % cmd)


def on_ack():
    logging.info('Incoming ACK.')


def on_ping():
    logging.info('Incoming PING. Sending sPONG.')
    stream.write('PONG')


def on_fetch(args):
    """Handles a new incoming content request.

    Prepares the response string and insert a new request element into the
    request pool. The element contains the request id, and response string."""

    ts = args[0]
    resource = args[1]

    logging.info('Request received %s' % resource)

    # also wrap the response data into the request pool.
    try:
        content = open(resource).read()
        status_code = 200
    except:
        content = 'Not found.'
        status_code = 404

    headers = {}
    #headers['Content-Length'] = len(content)
    headers_str = build_headers(headers, status_code)
    #response_content = headers_str + '\r\n{0}'.format(content)
    response_content = content
    request_pool.append({'response': response_content, 'ts': ts})


def authenticate():
    stream.write('IDENT {0} {1}{2}'.format(config['username'],
        config['password'], delimiter))


def process_commands(data):
    tokens = data.replace(delimiter, '').split(' ')
    cmd = tokens[0]
    args = tokens[1:]

    if cmd == 'ACK':
        on_ack()

    elif cmd == 'FETCH':
        on_fetch(args)

    elif cmd == 'PING':
        on_ping()

    elif cmd == 'DISCONNECT':
        on_disconnect()

    else:
        on_unrecognized(cmd)


def read_next_command():
    global delimiter
    global stream

    if stream.closed():
        logging.error('Stream closed while reading command line.')
        return False

    cmd_line = stream.read_until(delimiter)
    if cmd_line:
        print 'broke'

    print 'finished reading command'
    return process_commands(cmd_line)


class CrunchStream(object):
    def __init__(self, socket):
        self.socket = socket
        self.buffer = ''

    def write(self, data):
        #select.select([], [self.socket], [])
        data_size = len(data)
        sent_bytes = 0

        while sent_bytes < data_size:
            sent = self.socket.send(data)
            sent_bytes += sent
            data = data[sent:]

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


def start_reactor():
    while True:
        read_next_command()
        gevent.sleep(0)

def start_client(conf):
    global stream

    config = conf

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect((config['address'], config['port']))
    stream = CrunchStream(s)
    authenticate()

    # Create a RequestConveyor instance
    rc = RequestConveyor(stream, request_pool)
    rc.start()
    gevent.joinall([gevent.spawn(start_reactor), rc])


if __name__ == '__main__':
    config = {'port': 8080,
              'address': '192.241.244.33',
              'username': 'dash1291',
              'password': 'locker'}
    start_client(config)
