from __future__ import print_function

import sys

import tornadoredis
import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.gen
import logging

import redis

PY3 = sys.version > '3'
if PY3:
    xrange = range

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger('app')


POOL_ASYNC = tornadoredis.ConnectionPool(max_connections=500,
                                         wait_for_available=True)

REDIS_CLIENT = redis.Redis()


class AsyncIncr(tornado.web.RequestHandler):
    client_kwargs = {}

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        kk = ('f', 'b', 'z')
        cc = [tornadoredis.Client(**self.client_kwargs) for __ in kk]
        vals = yield [tornado.gen.Task(c.incr, k) for c, k in zip(cc, kk)]
        foo, bar, zar = ['%08d' % v for v in vals]
        self.set_header('Content-Type', 'text/html')
        self.render("template.html", title="Incr benchmark",
                    foo=foo, bar=bar, zar=zar)


class AsyncPooledIncr(AsyncIncr):
    client_kwargs = {'connection_pool': POOL_ASYNC}


class AsyncMset(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        c = tornadoredis.Client()
        num = 5000
        pairs = dict([('test%d' % d, 'val%d' % d) for d in xrange(0, num)])
        yield tornado.gen.Task(c.mset, pairs)
        kk = list(['test%d' % d for d in xrange(0, num)])
        vals = yield tornado.gen.Task(c.mget, kk)
        same = vals == ['val%d' % d for d in xrange(0, num)]
        foo, bar, zar = (num, len(vals), same)
        self.set_header('Content-Type', 'text/html')
        self.render("template.html", title="Incr benchmark",
                    foo=foo, bar=bar, zar=zar)


class SyncMset(tornado.web.RequestHandler):

    def get(self):
        c = REDIS_CLIENT
        num = 5000
        c.mset(dict([('test%d' % d, 'val%d' % d) for d in xrange(0, num)]))
        vals = c.mget(['test%d' % d for d in xrange(0, num)])
        same = vals == ['val%d' % d for d in xrange(0, num)]
        foo, bar, zar = (num, len(vals), same)
        self.set_header('Content-Type', 'text/html')
        self.render("template.html", title="Incr benchmark",
                    foo=foo, bar=bar, zar=zar)


class SyncIncr(tornado.web.RequestHandler):

    def get(self):
        c = REDIS_CLIENT
        vals = [c.incr(k) for k in ('f', 'b', 'z')]
        foo, bar, zar = ['%08d' % v for v in vals]
        self.set_header('Content-Type', 'text/html')
        self.render("template.html", title="Incr benchmark",
                    foo=foo, bar=bar, zar=zar)


application = tornado.web.Application([
    (r'/', AsyncIncr),
    (r'/redis-py/', SyncIncr),
    (r'/pool', AsyncPooledIncr),
    (r'/mset', AsyncMset),
    (r'/redis-py/mset', SyncMset),
])


if __name__ == '__main__':
    # Start the data initialization routine
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print('Benchmark is runing at 0.0.0.0:8888\n'
          'Quit the benchmark with CONTROL-C\n'
          'Use the following paths for benchmarking:\n'
          '  / - increment benchmark\n'
          '  /pool - connection pool benchmark\n'
          '  /mset - MSET benchmark\n'
          '  /redis-py/ - increment benchmark\n'
          '  /redis-py/mset - MSET benchmark')
    tornado.ioloop.IOLoop.instance().start()
