import logging
import argparse

import tornado.httpclient
import tornado.ioloop
import tornado.web
import tornado.gen

from cache import CacheMixin, MemoryCacheBackend


CACHE_SETTINGS = dict(
    CACHE_METHODS=['GET', 'POST'],
    CACHE_ENDPOINTS=[
        '/',
        '/api/slow-endpoint/',
    ],
    CACHE_TIMEOUT=60,
)


class ProxyHandler(tornado.web.RequestHandler, CacheMixin):
    # DO NOT proxy these headers (browser may raise an error)
    RESTRICTED_HEADERS = (
        'transfer-encoding',
        'content-length',
    )

    # DO NOT send body on these status codes
    RESTRICT_SEND_BODY_ON_CODE = (304, )

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def put(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def patch(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def head(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def options(self, *args, **kwargs):
        yield self.dispatch(*args, **kwargs)

    @tornado.gen.coroutine
    def dispatch(self, *args, **kwargs):
        """ Dispatch all http methods
        """
        cache_allowed = self.is_cache_allowed()
        logging.debug('%s: caching is %s', self.request.path, 'allowed' if cache_allowed else 'NOT allowed', )

        response = None
        cache_hit = False
        if cache_allowed:  # get from cache
            response = yield self.get_cached()
            cache_hit = True if response is not None else False
            logging.debug('%s: cache %s', self.request.uri, 'HIT' if cache_hit else 'MISS')

        if response is None:  # get actual
            response = yield self.proxy_async_request()

            if cache_allowed:
                if 200 <= response.code <= 299:  # store into cache
                    yield self.set_cache(response)
                    logging.debug('%s: status %d - stored in cache', self.request.uri, response.code)
                else:
                    logging.debug('%s: error status %d', self.request.uri, response.code)

        # output proxied response
        self.process_response(response)
        self.finish()

        if cache_allowed:
            if cache_hit:  # renew cache if cache hit
                yield self.renew_cache(self.proxy_async_request)
            logging.debug('%s: slow endpoint, cache %s', self.request.path, 'updated' if cache_hit else 'NOT updated')

    def process_response(self, response):
        """ Process proxied HTTP response to current
        """
        self.set_status(response.code)  # code
        for name, value in response.headers.items():  # headers except restricted
            if name.lower() not in self.RESTRICTED_HEADERS:
                self.set_header(name, value)
        if response.code not in self.RESTRICT_SEND_BODY_ON_CODE:  # body
            self.write(response.body)

    @tornado.gen.coroutine
    def proxy_async_request(self):
        # making transparent request
        headers = self.request.headers
        headers['Host'] = self.settings.get('uri')
        request = tornado.httpclient.HTTPRequest(
            url=self.make_server_uri() + self.request.uri,
            method=self.request.method,
            headers=headers,
            body=self.request.body if len(self.request.body) > 0 else None
        )
        # start async request
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield http.fetch(request, raise_error=False)

        return response

    def make_server_uri(self):
        return 'http://%s' % (self.settings.get('uri'), )


class Application(tornado.web.Application):
    """ Application with cache
    """
    def __init__(self, handlers=None, default_host="", transforms=None,
                 **settings):
        settings.update(CACHE_SETTINGS)
        self.cache = MemoryCacheBackend()
        super().__init__(handlers, default_host, transforms, **settings)


def parse_args():
    """ Parses arguments and return its values """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--server-uri', required=True, help='Server URI to proxy')
    argparser.add_argument('--host', help='Proxy address')
    argparser.add_argument('--port', type=int, help='Proxy port', default=8888)
    return argparser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()
    logging.info('Server run with arguments: %s', args)

    app = Application([
        (r".*", ProxyHandler),
    ], uri=args.server_uri)
    app.listen(args.port, address=args.host)
    tornado.ioloop.IOLoop.current().start()
