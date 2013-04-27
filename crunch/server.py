import pdb
import functools
import socket
import errno

from gevent import socket, spawn
from gevent.pool import Group
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer

from crunch.auth import SqliteDB
from crunch.http import CrunchHttp
from crunch.crunchlet import Crunchlet, CrunchStream


global_group = Group()
crunchpool = {}

def init_crunch(crunchpool, crunch_port=8890, database_path='crunch.db'):
    def connection_ready(sock, address):
        stream = CrunchStream(sock)
        crunchlet = Crunchlet(env, stream, address)
        crunchlet.start()
        crunchpool[str(address[0])] = crunchlet
        global_group.add(crunchlet)
        global_group.join()

    # Setup database interface
    database = SqliteDB('/Users/ashish/repos/crunch/crunch/crunch.db')

    # Prepare an env dict
    env = {
        'database': database,
        'crunchpool': crunchpool,
    }

    # Create socket and IO loop
    server = StreamServer(('0.0.0.0', crunch_port), connection_ready)
    server.serve_forever()

def init_http_server(http_port):
    return

def request_handler(environ, start_response):
    c_pool = CrunchHttp(crunchpool)
    #global_group.add(c_pool)
    #global_group.join()

    return c_pool.handle_request(environ, start_response)

def runserver(http_port=8888, crunch_port=8890):
    spawn(init_crunch, crunchpool, crunch_port)

    http_server = WSGIServer(('0.0.0.0', http_port), request_handler)
    http_server.serve_forever()

if __name__ == '__main__':
	runserver()