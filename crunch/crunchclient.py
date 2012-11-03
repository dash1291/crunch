import socket

from tornado import ioloop, iostream

delimiter = '\r\n\r\n'

def recv_data(callback):
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

    else:
        read_command()

def authenticate():
    send_data('IDENT ashish locker', read_command)

def read_command():
    recv_data(process_commands)

def on_fetch(args):
    ts = args[0]
    resource = args[1]
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
    response = 'CONTENT {0} {1}'.format(ts, response_content.encode('base64'))
    send_data(response, read_command)

def start_client(config):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    stream = iostream.IOStream(s)
    stream.connect((config['address'], config['port']), authenticate)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    config = {'port': 8890,
              'address': 'localhost'}
    start_client(config)