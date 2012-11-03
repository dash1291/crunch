import thread

from tornado import httpserver, ioloop

from crunchhttp import CrunchHttp
from crunchlets import init_crunch

crunchpool = {}

def runserver(http_port=8888, crunch_port=8890):
	thread.start_new(init_crunch, (crunchpool, crunch_port))
	http_server = httpserver.HTTPServer(CrunchHttp(crunchpool).handle_request)
	http_server.listen(http_port)
	ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	runserver()