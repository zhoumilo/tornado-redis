Tornado-Redis
=============

Asynchronous [Redis](http://redis.io/) client that works within [Tornado](http://tornadoweb.org/) IO loop.

This is basically a fork of [brükva](https://github.com/evilkost/brukva) redis client
slightly modified to work with tornado.gen interface instead of adisp.

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

Run redis-server on localhost:6379.
Run tests with the following command:

	python -m tornado.testing tornadoredis.tests

Reconnect tests have been disabled by default.

Credits
-------
brukva is developed and maintained by [Konstantin Merenkov](mailto:kmerenkov@gmail.com)

 * Inspiration: [redis-py](http://github.com/andymccurdy/redis-py)
 * Third-party software: [adisp](https://code.launchpad.net/adisp)


License
-------
See LICENSE file.
Long story short: WTFPL v2
