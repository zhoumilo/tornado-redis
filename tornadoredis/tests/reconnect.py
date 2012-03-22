from tornado import gen

from redistest import RedisTestCase, async_test


class ReconnectTestCase(RedisTestCase):
    @async_test
    @gen.engine
    def test_redis_timeout(self):
        res = yield gen.Task(self.client.setex, 'foo', 1, 'bar')
        self.assertEqual(res, True)

        @gen.engine
        def _get_delayed():
            res = yield gen.Task(self.client.get, 'foo')
            self.assertFalse(res)
            self.stop()
        self.delayed(2, _get_delayed)

    @async_test
    @gen.engine
    def test_redis_timeout_with_pipe(self):
        res = yield gen.Task(self.client.set, 'foo', 'bar')
        self.assertEqual(res, True)
        pipe = self.client.pipeline(transactional=True)
        pipe.get('foo')
        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, ['bar'])
        self.stop()
