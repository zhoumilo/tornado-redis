#!/usr/bin/env python
from functools import partial
from random import randint

from tornado import gen

import tornadoredis

from redistest import RedisTestCase
from tornadoredis.exceptions import ConnectionError
from tornadoredis.tests.redistest import async_test


class ConnectionPoolTestCase(RedisTestCase):

    def _new_pool(self, **connection_params):
        connection_params.setdefault('io_loop', self.io_loop)
        connection_params.setdefault('max_connections', 2)
        return tornadoredis.ConnectionPool(**connection_params)

    @gen.engine
    def _set_random_using_new_connection(self, pool, key, callback=None):
        c1 = self._new_client(pool)
        v1 = '%d' % randint(1, 1000)
        yield gen.Task(c1.set, key, v1)
        yield gen.Task(c1.disconnect)
        self.io_loop.add_callback(partial(callback, v1))

    def test_max_connections(self):
        pool = self._new_pool(max_connections=2)
        c1 = self._new_client(pool=pool)
        c2 = self._new_client(pool=pool)
        self.assertRaises(ConnectionError,
                          partial(self._new_client, pool=pool))

    @async_test
    @gen.engine
    def test_wait_for_available(self):
        pool = self._new_pool(max_connections=2, wait_for_available=True)
        keys = ['foo%d' % n for n in xrange(1, 5)]
        vals = yield [gen.Task(self._set_random_using_new_connection, pool, k)
                      for k in keys]
        c3 = self._new_client(pool)
        vals_saved = yield gen.Task(c3.mget, keys)
        self.assertEqual(vals, vals_saved)

        self.stop()

    @async_test
    @gen.engine
    def test_reconnect(self):
        pool = self._new_pool(max_connections=1, wait_for_available=True)
        c = self._new_client(pool)
        v1 = '%d' % randint(1, 1000)
        v2 = '%d' % randint(1, 1000)
        yield gen.Task(c.set, 'foo1', v1)
        yield gen.Task(c.disconnect)
        yield gen.Task(c.set, 'foo2', v2)
        yield gen.Task(c.disconnect)
        v1_saved, v2_saved = yield gen.Task(c.mget, ('foo1', 'foo2'))
        yield gen.Task(c.disconnect)
        self.assertEqual(v1, v1_saved)
        self.assertEqual(v2, v2_saved)

        # Do the same thing with anither client instance
        c = self._new_client(pool)
        v1 = '%d' % randint(1, 1000)
        v2 = '%d' % randint(1, 1000)
        yield gen.Task(c.set, 'foo1', v1)
        yield gen.Task(c.disconnect)
        yield gen.Task(c.set, 'foo2', v2)
        yield gen.Task(c.disconnect)
        v1_saved, v2_saved = yield gen.Task(c.mget, ('foo1', 'foo2'))
        self.assertEqual(v1, v1_saved)
        self.assertEqual(v2, v2_saved)

        self.stop()

    @async_test
    @gen.engine
    def test_connection_pool(self):
        pool = self._new_pool(max_connections=1)
        v1 = yield gen.Task(self._set_random_using_new_connection,
                            pool, 'foo1')
        v2 = yield gen.Task(self._set_random_using_new_connection,
                            pool, 'foo2')
        c3 = self._new_client(pool)
        v1_saved, v2_saved = yield gen.Task(c3.mget, ('foo1', 'foo2'))
        self.assertEqual(v1, v1_saved)
        self.assertEqual(v2, v2_saved)

        self.stop()

    @async_test
    @gen.engine
    def test_for_memory_leaks(self):
        '''
        Find and test the way to destroy client instances in
        tornado.gen-wrapped functions if the connection_pool is used.
        Still had no luck with it.
        '''
        @gen.engine
        def some_code(pool, on_client_destroy=None, callback=None):
            c = self._new_client(pool=pool,on_destroy=on_client_destroy)
            n = '%d' % randint(1, 1000)
            yield gen.Task(c.set, 'foo', n)
            n2 = yield gen.Task(c.get, 'foo')
            self.assertEqual(n, n2)

            callback(True)

        pool = self._new_pool(max_connections=1)

        for __ in xrange(1, 3):
            yield gen.Task(some_code, pool,
                           on_client_destroy=(yield gen.Callback('destroy')))
            yield gen.Wait('destroy')

        self.stop()
