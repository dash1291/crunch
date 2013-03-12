import thread
import functools
import socket
import errno

from tornado import httpserver, ioloop

from crunch.http import CrunchHttp
from crunch.crunchlet import init_crunch

crunchpool = {}

def init_crunch(crunchpool, crunch_port=8890, database_path = 'crunch.db'):
    def connection_ready(sock, io_loop, fd, events):
        while True:
            try:
                connection, address = sock.accept()
                stream = iostream.IOStream(connection)
                crunchlet = CrunchLet(env, stream, address)
                crunchpool[str(address)] = crunchlet
            except socket.error, e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                return
            connection.setblocking(0)
            crunchlet.handle_connection()

    # Setup database interface
    database = SqliteDB(database_path)

    # Prepare an env dict
    env['database'] = database
    env['crunchpool'] = crunchpool
    env['ioloop'] = io_loop

    # Create socket and IO loop
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(("", crunch_port))
    sock.listen(128)

    io_loop = ioloop.IOLoop.instance()
    callback = functools.partial(connection_ready, sock, io_loop)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    io_loop.start()

def runserver(http_port=8888, crunch_port=8890):
	thread.start_new(init_crunch, (crunchpool, crunch_port))
	http_server = httpserver.HTTPServer(CrunchHttp(crunchpool).handle_request)
	http_server.listen(http_port)
	ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	runserver()