import re

class Handler():
    def __init__(self, request):
        self.uri = request.uri
        a = self.parse_uri()
        message = a
        request.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s" % (
                     len(message), message))
        request.finish()

    def parse_uri(self):
        uri = self.uri
        resource_name = re.search('/([^/]+)', uri)
        try:
            args = resource_name.group(1)
        except:
            args = ''
        return args