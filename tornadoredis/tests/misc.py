import gc
from tornado import gen

from tornadoredis.exceptions import ResponseError

from redistest import RedisTestCase, async_test


class MiscTestCase(RedisTestCase):
    @async_test
    @gen.engine
    def test_response_error(self):
        res = yield gen.Task(self.client.set, 'foo', 'bar')
        self.assertTrue(res)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertIsInstance(res, ResponseError)
        self.stop()

#    @async_test
#    @gen.engine
#    def test_for_memory_leaks(self):
#        '''
#        Tests if a Client instance destroyed properly
#        '''
#        def some_code(callback=None):
#            c = self._new_client(on_destroy=callback)
#            c.get('foo')
#
#        for __ in xrange(1, 3):
#            yield gen.Task(some_code)
#
#        self.stop()
#
#    @async_test
#    @gen.engine
#    def test_for_memory_leaks_gen(self):
#        '''
#        Find and test the way to destroy client instances in
#        tornado.gen-wrapped functions.
#        '''
#        @gen.engine
#        def some_code(on_destroy=None, callback=None):
#            c1 = self._new_client(on_destroy=on_destroy)
#            yield gen.Task(c1.get, 'foo')
#            callback(True)
#
#
#        yield gen.Task(some_code, on_destroy=(yield gen.Callback('destroy')))
#        yield gen.Wait('destroy')
#
#        self.stop()
