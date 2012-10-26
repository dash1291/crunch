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
    except:
        content = 'Not found.'
        
    response = 'CONTENT {0} {1}'.format(ts, content)
    send_data(response, read_command)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
stream = iostream.IOStream(s)
stream.connect(('localhost', 8890), authenticate)
ioloop.IOLoop.instance().start()