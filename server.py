import thread

from tornado import httpserver, ioloop

from handler import Handler
from crunchlets import init_crunch

crunchpool = {}

thread.start_new(init_crunch, (crunchpool,))
http_server = httpserver.HTTPServer(Handler)
http_server.listen(8888)
ioloop.IOLoop.instance().start()
