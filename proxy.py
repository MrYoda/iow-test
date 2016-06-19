import logging
import argparse

import tornado.httpclient
import tornado.ioloop
import tornado.web


class ProxyHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def put(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def delete(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def patch(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def head(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    @tornado.web.asynchronous
    def options(self, *args, **kwargs):
        return self.proxy_request(*args, **kwargs)

    def proxy_request(self, *args, **kwargs):
        # todo: check cache for stored result

        # making transparent request
        request = tornado.httpclient.HTTPRequest(
            url=self.settings.get('uri') + self.request.path,
            method=self.request.method,
            headers=self.request.headers,
            body=self.request.body if len(self.request.body) > 0 else None
        )
        # start async request
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(request, callback=self.on_response)

    def on_response(self, response):
        if 200 <= response.code < 300:  # OK
            pass  # todo: caching result
        self.write(response.body)  # todo: transparent result return
        self.finish()


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
