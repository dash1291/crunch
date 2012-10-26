import socket

from tornado import ioloop, iostream

delimiter = '\r\n\r\n'

def read_command():
    stream.read_until(delimiter, on_headers)

def on_headers(data):
    data = data.replace('\r\n\r\n', '')
    print '<< ' + data
    tokens = data.split(' ')
    ts = tokens[1]
    resource = tokens[2]
    content = open(resource).read()
    response = 'CONTENT %s %s' % (ts, content)
    print '>> ' + response
    stream.write(response + delimiter)
    read_command()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
stream = iostream.IOStream(s)
stream.connect(('localhost', 8890), read_command)
ioloop.IOLoop.instance().start()