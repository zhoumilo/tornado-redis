Tornado-Redis
=============

Asynchronous [Redis](http://redis.io/) client for the [Tornado Web Server](http://tornadoweb.org/).

This is a fork of [brükva](https://github.com/evilkost/brukva) redis client
modified to be used via Tornado's native 'tornado.gen' interface instead
of 'adisp' call dispatcher.

Tornado-Redis is licensed under the Apache Licence, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0.html).

Usage
-----

	import tornadoredis
	import tornado.web
	import tornado.gen

	...	
	
	c = tornadoredis.Client()
	c.connect()

	...

	class MainHandler(tornado.web.RequestHandler):
	    @tornado.web.asynchronous
	    @tornado.gen.engine
	    def get(self):
	        foo = yield tornado.gen.Task(c.get, 'foo')
	        bar = yield tornado.gen.Task(c.get, 'bar')
	        zar = yield tornado.gen.Task(c.get, 'zar')
	        self.set_header('Content-Type', 'text/html')
	        self.render("template.html", title="Simple demo", foo=foo, bar=bar, zar=zar)

Tips on testing
---------------

The redis server must be started on the default (:6379) port.

Use this command to run the test suite:

	python -m tornado.testing tornadoredis.tests

'Autoreconnect' feature tests have been disabled by default.
To enable them open the tornadoredis/test/__init__.py file and
remove the '#' character from the line looking like this:
 
    # from reconnect import ReconnectTestCase

Make sure you've configured redis-server to drop client connections by timeout
before running reconnect tests.

Credits and Contributors
------------------------
The brukva project has been started by [Konstantin Merenkov](mailto:kmerenkov@gmail.com)
but seem to be not maintained any more. 

[evilkost](https://github.com/evilkost)

[mattd](https://github.com/mattd)

[maeldur](https://github.com/maeldur)

The Tornado-Redis project's source code and 'tornado-redis' PyPI package
are maintained by [leporo](https://github.com/leporo)
