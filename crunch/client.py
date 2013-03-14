import socket
import threading

from tornado import ioloop, iostream

delimiter = '\r\n\r\n'
stream = None
config = None
request_pool = []


class RequestConveyor(threading.Thread):
    """Thread that does rotation of requests in the request pool.

    Response for each request is written to the stream one piece (i.e. of
    length given by STREAM_LENGTH) at a time."""

    def __init__(self, request_pool, stream, stream_length=32):
        self.request_pool = request_pool
        self.stream = stream
        self.stream_length = stream_length

    def run(self):
        STREAM_LENGTH = self.stream_length

        while True:
            for request in self.request_pool:
                ts = request['ts']
                response_content = request['response']

                # write data into the stream one piece at a time
                if len(response_content) > 3:
                    resp_stream = response_content[:STREAM_LENGTH]
                    response_content = response_content[STREAM_LENGTH:]
                else:
                    resp_stream = response_content[:len(response_content)]
                    response_content = ''
                    self.request_pool

                response = 'CONTENT {0} {1}'.format(ts, resp_stream)
                send_data(response, read_command)



def recv_data(callback, bytes = None):
    if stream.closed():
        return False

    while stream.reading() == True:
        continue

    def onrecv(data):
        data = data.replace(delimiter, '')
        print '<< ' + data
        callback(data)

    stream.read_until(delimiter, onrecv)

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

def send_data(data, callback):
    if stream.closed():
        return False

    print '>> '  + data
    stream.write(data + delimiter, callback)

def process_commands(data):
    tokens = data.split(' ')
    cmd = tokens[0]
    args = tokens[1:]

    if cmd == 'ACK':
        read_command()

    elif cmd == 'FETCH':
        on_fetch(args)
    elif cmd == 'PING':
        send_data('PONG', read_command)
    elif cmd == 'DISCONNECT':
        stream.close()

    else:
        read_command()

def authenticate():
    send_data('IDENT {0} {1}'.format(config['username'], config['password']),
        read_command)

def read_command():
    recv_data(process_commands)

def on_fetch(args):
    """Handles a new incoming content request.
    
    Prepares the response string and insert a new request element into the 
    request pool. The element contains the request id, and response string."""
    
    ts = args[0]
    resource = args[1]

    # also wrap the response data into the request pool.
    try:
        content = open(resource).read()
        status_code = 200
    except:
        content = 'Not found.'
        status_code = 404

    headers = {}
    headers['Content-Length'] = len(content)
    headers_str = build_headers(headers, status_code)
    response_content = headers_str + '\r\n{0}'.format(content)

    request_pool.append({'id': request_id, 'response': 
        response_content.encode('base64'), 'ts': ts})

def start_client(conf):
    global stream
    global config
    config = conf

    # Create a RequestConveyor instance
    rc = RequestConveyor(stream, http_pool)
    rc.start()

    # Initialize the IOLoop
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    stream = iostream.IOStream(s)
    stream.connect((config['address'], config['port']), authenticate)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    config = {'port': 8890,
              'address': 'localhost'}
    start_client(config)