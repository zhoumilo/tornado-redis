from tornado import gen

from redistest import RedisTestCase, async_test
from tornadoredis.exceptions import ResponseError


class MiscTestCase(RedisTestCase):
    @async_test
    @gen.engine
    def test_response_error(self):
        res = yield gen.Task(self.client.set, 'foo', 'bar')
        self.assertTrue(res)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertIsInstance(res, ResponseError)
        self.stop()
