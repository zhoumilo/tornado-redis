SockJS Demo
===========

This application demonstrates the usage of SockJSSubscriber class to
subscribe clients connected using SockJS library to a messages send to
a redis channel.

Please note that this demo is very similar to the 'Websockets' demo but
utilizes a single redis server connection for all subscribed clients.

Application opens two channel subscriptions for each connected clients: one
for the broadcast messages and one for private messages, sent to this user.

Running Demo
------------

To run this demo please install required packages:

    pip install -r tornado sockjs-tornado

If you have tornado-redis installed in your environment you may
start the demo server form the sockjs demo folder:

    python app.py

To run demo from the tornado-redis repository working copy folder
you may use this command:

    PYTHONPATH=. python demos/sockjs/app.py

To see demo in action please connect to http://127.0.0.1:8888 using
your web browser.
