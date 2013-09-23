import re

from gevent.event import AsyncResult


class CrunchHttp():
    def __init__(self, crunchpool):
        self.response_buffer = ''
        self.async_response = AsyncResult()
        self.response_headers = AsyncResult()
        self.crunchpool = crunchpool
        self._finished = False

    """WSGI handler."""
    def handle_request(self, environ, start_response):
        self.uri = environ['PATH_INFO']
        uri_opts = self.parse_uri()

        status = '200 OK'
        if not uri_opts == None:
            result = self.process_opts(uri_opts)
            if result == False:
                #self.write_response('Not found.', 404, True)
                status = '404 Not Found'
        else:
            #self.write_response('Not found.', 404, True)
            status = '404 Not Found'

        headers = []
        start_response(status, headers)

        while self._finished == False:
            yield self.async_response.get()
            self.async_response = AsyncResult()

    def build_headers(self, headers, status_code):
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

    def write_headers(self, headers):
        self.response_headers.set(headers)

        headers_str = self.build_headers(headers)
        self.request.write(headers_str)

    def write_response(self, response, status_code=200, build_headers=False):
        self.response_buffer = response
        self.async_response.set(response)
        if build_headers == True:
            headers = {}
            #headers['Content-Length'] = len(response)
            headers_str = self.build_headers(headers, status_code)
            response = headers_str + '\r\n{0}'.format(response)

    def finish(self):
        self.async_response.set('')
        self._finished = True

    def process_opts(self, uri_opts):
        found = False

        for crunchlet in self.crunchpool.values():
            if crunchlet.uid == uri_opts['node_name']:
                found = True
                crunchlet.send_fetch(uri_opts['resource_name'], self)

        return found

    def parse_uri(self):
        uri = self.uri
        args = {}
        re_match = re.search('/([^/]+)/([^/]+)', uri)

        try:
            args['node_name'] = re_match.group(1)
            args['resource_name'] = re_match.group(2)
        except:
            return None

        return args
