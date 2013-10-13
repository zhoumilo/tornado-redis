from __future__ import print_function

import os.path

import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen

import redis
import tornadoredis
import tornadoredis.pubsub

try:
    import sockjs.tornado
except:
    print('Please install the sockjs-tornado package to run this demo.')
    exit(1)


# Use the synchronous redis client to publish messages to a channel
redis_client = redis.Redis()
# Create the tornadoredis.Client instance
# and use it for redis channel subscriptions
subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())


class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template.html", title="PubSub + SockJS Demo")


class SendMessageHandler(tornado.web.RequestHandler):
    def post(self):
        message = self.get_argument('message')
        redis_client.publish('test_channel', message)
        self.set_header('Content-Type', 'text/plain')
        self.write('sent: %s' % (message,))


class MessageHandler(sockjs.tornado.SockJSConnection):
    """
    SockJS connection handler.

    Note that there are no "on message" handlers - SockJSSubscriber class
    utilizes SockJSConnection.broadcast method to transfer messages
    to subscribed clients.
    """
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        subscriber.subscribe('test_channel', self)

    def on_close(self):
        subscriber.unsubscribe('test_channel', self)


application = tornado.web.Application(
    [(r'/', IndexPageHandler),
     (r'/send_message', SendMessageHandler)] +
    sockjs.tornado.SockJSRouter(MessageHandler, '/sockjs').urls)


if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print('Demo is runing at 0.0.0.0:8888\n'
          'Quit the demo with CONTROL-C')
    tornado.ioloop.IOLoop.instance().start()
