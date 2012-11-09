import socket
from functools import partial

from tornado import gen
from tornado.netutil import TCPServer

from tornado.testing import AsyncTestCase

import tornadoredis
from tornadoredis.exceptions import ConnectionError
from tornadoredis.tests.redistest import async_test, RedisTestCase


class DisconnectingRedisServer(TCPServer):

    def disconnect(self):
        # Using a single stream for testing
        stream = self._stream
        try:
            stream.socket.shutdown(socket.SHUT_RDWR)
            stream.close()
        except socket.error:
            pass

    @gen.engine
    def handle_stream(self, stream, address):
        self._stream = stream
        n_args = yield gen.Task(stream.read_until, '\r\n')
        while n_args and n_args[0] == '*':
            yield gen.Task(stream.read_until, '\r\n')
            yield gen.Task(stream.read_until, '\r\n')
            # Read command arguments
            arg_num = int(n_args.strip()[1:]) - 1
            if arg_num > 0:
                for __ in xrange(0, arg_num):
                    # read the $N line
                    yield gen.Task(stream.read_until, '\r\n')
                    # read the argument line
                    yield gen.Task(stream.read_until, '\r\n')
            stream.write('+OK\r\n')
            # Read the next command
            n_args = yield gen.Task(stream.read_until, '\r\n')
        self._stream = None


# RedisTestCase
class DisconnectTestCase(AsyncTestCase):
    test_db = 9
    test_port = 6380

    def setUp(self):
        #self._server_io_loop = IOLoop()
        # self._server_io_loop
        super(DisconnectTestCase, self).setUp()
        self._server = DisconnectingRedisServer(io_loop=self.io_loop)
        self._server.listen(self.test_port)
        self.client = self._new_client()
        self.client.flushdb()

    def _new_client(self):
        client = tornadoredis.Client(io_loop=self.io_loop,
                                     port=self.test_port,
                                     selected_db=self.test_db)
        # client.connection.connect()
        # client.select(self.test_db)
        return client

    def tearDown(self):
        try:
            self.client.connection.disconnect()
            del self.client
        except AttributeError:
            pass
        self._server.stop()
        super(DisconnectTestCase, self).tearDown()

    def test_disconnect(self):
        def _disconnect_and_send_a_command():
            self.client.set('foo', 'bar', callback=self.stop)
            self.wait()
            self._server.disconnect()
            self._server.stop()
            self.client.set('foo', 'bar', callback=self.stop)
            self.wait()
        self.assertRaises(ConnectionError, _disconnect_and_send_a_command)

    def test_reconnect(self):
        def _test_send():
            self.client.set('foo', 'bar', callback=self.stop)
            self.wait()

        _test_send()
        self._server.disconnect()
        _test_send()
        self.stop()
