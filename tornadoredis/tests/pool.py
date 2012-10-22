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

    def _new_client(self, pool=None):
        client = tornadoredis.Client(connection_pool=pool)
        # client.connection.connect()
        client.select(self.test_db)
        return client

    @gen.engine
    def _set_random_using_new_connection(self, pool, key, callback=None):
        c1 = self._new_client(pool)
        v1 = '%d' % randint(1, 1000)
        yield gen.Task(c1.set, key, v1)
        c1.disconnect()
        callback(v1)

    def test_max_connections(self):
        return
        pool = self._new_pool(max_connections=2)
        self._new_client(pool=pool)
        self._new_client(pool=pool)
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
