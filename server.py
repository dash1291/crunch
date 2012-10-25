import thread

from tornado import httpserver, ioloop

from crunchhttp import CrunchHttp
from crunchlets import init_crunch

crunchpool = {}

thread.start_new(init_crunch, (crunchpool,))

http_server = httpserver.HTTPServer(CrunchHttp(crunchpool).handle_request)
http_server.listen(8888)
ioloop.IOLoop.instance().start()
