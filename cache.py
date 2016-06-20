import time
import pickle
from hashlib import sha1
import tornado.gen


class CacheMixin:
    """ Caching mixin for tornado handlers
    """
    def is_cache_allowed(self):
        """ Return True if HTTP method and path allowed to caching
        """
        return self.request.method.upper() in self.settings.get('CACHE_METHODS')\
               and self.request.path in self.settings.get('CACHE_ENDPOINTS')

    @tornado.gen.coroutine
    def get_cached(self):
        """ Retrieve response from cache
        """
        key = self._generate_key(self.request)
        return self.cache.get(key)

    @tornado.gen.coroutine
    def set_cache(self, response):
        """ Store response to cache
        """
        key = self._generate_key(self.request)
        self.cache.set(key, response, self.settings.get('CACHE_TIMEOUT'))

    @tornado.gen.coroutine
    def renew_cache(self, method):
        """ Renew cache for particular endpoints
        """
        if self.request.path in self.settings.get('CACHE_ENDPOINTS'):
            response = yield method()
            if 200 <= response.code <= 299:
                self.set_cache(response)


    @property
    def cache(self):
        """ Cache backend from tornado app
        """
        return self.application.cache

    @property
    def settings(self):
        """ Settings from tornado app
        """
        return self.application.settings

    def _generate_key(self, request):
        """ Generates key for cache storing
        """
        key = pickle.dumps((request.path, request.arguments))
        return "cache:%s" % sha1(key).hexdigest()


class CacheBackend:
    """ The base cache backend class
    """

    def get(self, key):
        raise NotImplementedError

    def set(self, key, value, timeout):
        raise NotImplementedError

    def delitem(self, key):
        raise NotImplementedError

    def exists(self, key):
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """ Simple memory cache backend
    Stores data in simple dict objects
    """
    CACHE = None  # cache data in format "key: value"
    CACHE_EXPIRED = None  # cache expires data in format "key: timestamp"

    def __init__(self):
        self.CACHE = dict()
        self.CACHE_EXPIRED = dict()

    def get(self, key):
        """ Return exists and actual value of key """
        if self.exists(key) and not self.is_expired(key):
            return self.CACHE.get(key)

        return None

    def set(self, key, value, timeout=None):
        """ Set value and expire timestamp for key """
        self.CACHE[key] = value
        if timeout:
            self.CACHE_EXPIRED[key] = self._get_timestamp() + timeout
        else:
            self.CACHE_EXPIRED[key] = 0

    def delitem(self, key):
        """ Delete key """
        del self.CACHE[key]
        del self.CACHE_EXPIRED[key]

    def exists(self, key):
        """ Check is key exists in cache """
        return key in self.CACHE

    def is_expired(self, key):
        """ Return True if key has non-zero value less than current timestamp """
        return self.CACHE_EXPIRED.get(key, 0) and self.CACHE_EXPIRED[key] <= self._get_timestamp()

    @staticmethod
    def _get_timestamp():
        """ Return current timestamp """
        return int(time.time())
