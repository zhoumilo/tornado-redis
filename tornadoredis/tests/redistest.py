#!/usr/bin/env python
import time

from tornado.testing import AsyncTestCase

import tornadoredis


def get_callable(obj):
    return hasattr(obj, '__call__')


def async_test(meth):
    def _runner(self, *args, **kwargs):
        try:
            meth(self, *args, **kwargs)
        except:
            self.stop()
            raise
        return self.wait()
    return _runner


class RedisTestCase(AsyncTestCase):
    def setUp(self):
        super(RedisTestCase, self).setUp()
        self.client = self._new_client()
        self.client.flushdb()

    def tearDown(self):
        try:
            self.client.connection.disconnect()
            del self.client
        except AttributeError:
            pass
        super(RedisTestCase, self).tearDown()

    def _new_client(self):
        client = tornadoredis.Client(io_loop=self.io_loop)
        client.connection.connect()
        client.select(9)
        return client

    def delayed(self, timeout, cb):
        self.io_loop.add_timeout(time.time()+timeout, cb)
