import re

class CrunchHttp():
    def __init__(self, crunchpool):
        self.crunchpool = crunchpool

    def handle_request(self, request):
        self.uri = request.uri
        self.request = request
        uri_opts = self.parse_uri()
        self.process_opts(uri_opts)
        
    def write_response(self, response):
        request = self.request
        request.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s" % (
                     len(message), message))
        request.finish()

    def process_opts(self, uri_opts):
        content = ''
        print self.crunchpool
        for crunchlet in self.crunchpool.values():
            #if crunchlet.name == uri_opts['node_name']:
            content = crunchlet.fetch(uri_opts['resource_name'], self) 
        return content

    def parse_uri(self):
        uri = self.uri
        args = {}
        re_match = re.search('/([^/]+)/([^/]+)', uri)
        try:
            args['node_name'] = re_match.group(1)
            args['resource_name'] = re_match.group(2)
        except:
            raise Exception('Insufficient URI')
        return args