import os.path
import sys

import gevent
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crunch.auth import SqliteDB
from crunch.http import CrunchHttp
from crunch.crunchlet import Crunchlet, CrunchStream


crunchpool = {}

def init_crunch(crunchpool, crunch_port=8890, database_path='crunch.db'):
    print 'crunch init'
    def connection_ready(sock, address):
        stream = CrunchStream(sock)
        crunchlet = Crunchlet(env, stream, address)
        crunchlet.start()
        crunchpool[str(address[0]) + ':' + str(address[1])] = crunchlet

    # Setup database interface
    database = SqliteDB(os.path.join(os.path.dirname(__file__), 'crunch.db'))

    # Prepare an env dict
    env = {
        'database': database,
        'crunchpool': crunchpool,
    }

    # Create socket and IO loop
    server = StreamServer(('0.0.0.0', crunch_port), connection_ready)
    server.serve_forever()


def request_handler(environ, start_response):
    c_pool = CrunchHttp(crunchpool)
    return c_pool.handle_request(environ, start_response)


def init_http_server(http_port=8888, crunch_port=8890):
    print 'web initialized'
    http_server = WSGIServer(('0.0.0.0', http_port), request_handler)
    http_server.serve_forever()


def runserver(http_port=8888, crunch_port=8890):
    gevent.joinall([gevent.spawn(init_http_server, http_port, crunch_port),
                    gevent.spawn(init_crunch, crunchpool, crunch_port)])


if __name__ == '__main__':
    runserver()
