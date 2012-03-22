from tornado import gen

from tornadoredis import Client

from redistest import RedisTestCase, async_test


class PubSubTestCase(RedisTestCase):

    def setUp(self):
        super(PubSubTestCase, self).setUp()
        self._message_count = 0
        self.publisher = self._new_client()

    def tearDown(self):
        try:
            self.publisher.connection.disconnect()
            del self.publisher
        except AttributeError:
            pass
        super(PubSubTestCase, self).tearDown()

    def _expect_messages(self, messages):
        self._expected_messages = messages

    def _handle_message(self, msg):
        self._message_count += 1
        self.assertIn(msg.kind, self._expected_messages)
        expected = self._expected_messages[msg.kind]
        self.assertEqual(msg.channel, expected[0])
        self.assertEqual(msg.body, expected[1])

    @async_test
    @gen.engine
    def test_pub_sub(self):
        self._expect_messages({'subscribe': ('foo', 1),
                               'message': ('foo', 'bar'),
                               'unsubscribe': ('foo', 0)})

        yield gen.Task(self.client.subscribe, 'foo')
        self.client.listen(self._handle_message)
        yield gen.Task(self.publisher.publish, 'foo', 'bar')
        yield gen.Task(self.client.unsubscribe, 'foo')
        
        self.assertEqual(self._message_count, 3)
        self.stop()

    @async_test
    @gen.engine
    def test_pub_psub(self):
        self._expect_messages({'psubscribe': ('foo.*', 1),
                               'pmessage': ('foo.*', 'bar'),
                               'punsubscribe': ('foo.*', 0),
                               'unsubscribe': ('foo.*', 1)})

        yield gen.Task(self.client.psubscribe, 'foo.*')
        self.client.listen(self._handle_message)
        yield gen.Task(self.publisher.publish, 'foo.1', 'bar')
        yield gen.Task(self.publisher.publish, 'bar.1', 'zar')
        yield gen.Task(self.client.punsubscribe, 'foo.*')
        
        self.assertEqual(self._message_count, 3)
        self.stop()
'''
    @async_test
    @gen.engine
    def test_unsubscribe(self):
        global c
        c = 0
        def on_recv(msg):
            if isinstance(msg, Exception):
                self.fail('Got unexpected exception: %s' % msg)

            global c
            if c == 0:
                self.assert_pubsub(msg, 'message', 'foo', 'bar')
            elif c == 1:
                self.assert_pubsub(msg, 'message', 'so', 'much')
            c += 1

        def on_subscription(msg):
            self.assert_pubsub(msg, 'subscribe', 'foo', 1)
            yield gen.Task(self.client.listen, on_recv)

        yield gen.Task(self.client.subscribe, 'foo', on_subscription)
        yield gen.Task(self.client.publish, 'foo', 'bar')
        self.delayed(0.2, self.client.subscribe('so',))
        self.delayed(0.3, lambda: self.client.unsubscribe('foo'))
        self.delayed(0.4, lambda: self.client.publish('so', 'much'))
        self.delayed(0.5, lambda: self.client.nsubscribe('so'))
        self.delayed(0.6, lambda: self.client.set('zar', 'xar', self.expect(True)))
        self.stop()

    @async_test
    @gen.engine
    def test_pub_sub_disconnect(self):
        def on_recv(msg):
            self.assertIsInstance(msg, ConnectionError)

        def on_subscription(msg):
            self.assertEqual(msg.kind, 'subscribe')
            self.assertEqual(msg.channel, 'foo')
            self.assertEqual(msg.body, 1)
            yield gen.Task(self.client.listen, on_recv)

        def on_publish(value):
            self.assertIsNotNone(value)

        yield gen.Task(self.client.subscribe, 'foo', on_subscription)
        self.client.disconnect()
        yield gen.Task(self.client.publish, 'foo', 'bar', on_publish)
        yield gen.Task(self.client.publish, 'foo', 'bar', on_publish)
        self.stop()
'''