import logging
import argparse

import tornado.httpclient
import tornado.ioloop
import tornado.web
import tornado.gen


class ProxyHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def put(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def patch(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def head(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def options(self, *args, **kwargs):
        yield self.proxy_request(*args, **kwargs)

    @tornado.gen.coroutine
    def proxy_request(self, *args, **kwargs):
        response = yield self.proxy_async_request()

        self.write(response.body)
        self.finish()

    @tornado.gen.coroutine
    def proxy_async_request(self):
        # making transparent request
        request = tornado.httpclient.HTTPRequest(
            url=self.settings.get('uri') + self.request.uri,
            method=self.request.method,
            headers=self.request.headers,
            body=self.request.body if len(self.request.body) > 0 else None
        )
        # start async request
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield http.fetch(request, raise_error=False)

        return response


def make_app(uri):
    """ Makes tornado app instance """
    return tornado.web.Application([
        (r".*", ProxyHandler),
    ], uri=uri)


def parse_args():
    """ Parses arguments and return its values """
    argparser = argparse.ArgumentParser()
    # argparser.add_argument('-u', '--uri', required=True, help='Server URI to proxy')
    argparser.add_argument('-u', '--uri', required=False, help='Server URI to proxy', default='http://ya.ru')
    argparser.add_argument('-H', '--host', help='Proxy address')
    argparser.add_argument('-p', '--port', type=int, help='Proxy port', default=8888)
    return argparser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()
    logging.info('Server arguments: %s', args)

    app = make_app(args.uri)
    app.listen(args.port, address=args.host)
    tornado.ioloop.IOLoop.current().start()
