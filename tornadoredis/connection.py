import socket
from functools import partial
import weakref
from collections import deque
from itertools import chain

from tornado.iostream import IOStream

from .exceptions import ConnectionError


class Connection(object):
    def __init__(self, host='localhost', port=6379, event_handler=None,
                 stop_after=None, io_loop=None):
        self.host = host
        self.port = port
        self.set_event_handler(event_handler)
        self.timeout = stop_after
        self._stream = None
        self._io_loop = io_loop

        self.in_progress = False
        self.read_callbacks = []
        self.ready_callbacks = deque()
        self._lock = 0

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self._lock += 1
        return self

    def __exit__(self, *args, **kwargs):
        self._lock -= 1
        if not self._lock:
            self.continue_pending()

    def continue_pending(self):
        # Continue with pending command execution
        # if all read operations are completed.
        if not self.read_callbacks and self.ready_callbacks:
            # Pop a SINGLE callback from the queue and execute it.
            # The next one will be executed from the code
            # invoked by the callback
            callback = self.ready_callbacks.popleft()
            callback()

    def set_event_handler(self, event_handler):
        if event_handler:
            self._event_handler = weakref.proxy(event_handler)
        else:
            self._event_handler = None

    def ready(self):
        return (not self._lock and
                not self.read_callbacks
                and not self.ready_callbacks)

    def wait_until_ready(self, callback=None):
        if callback:
            if not self.ready():
                self.ready_callbacks.append(callback)
            else:
                callback()
        return self

    def connect(self):
        if not self._stream:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                self._stream = IOStream(sock, io_loop=self._io_loop)
                self._stream.set_close_callback(self.on_stream_close)
            except socket.error, e:
                raise ConnectionError(str(e))
            self.fire_event('on_connect')

    def on_stream_close(self):
        if self._stream:
            self._stream = None
            callbacks = self.read_callbacks
            self.read_callbacks = []
            for callback in callbacks:
                callback(None)

    def disconnect(self):
        if self._stream:
            s = self._stream
            self._stream = None
            try:
                if s.socket:
                    s.socket.shutdown(socket.SHUT_RDWR)
                s.close()
            except socket.error:
                pass

    def fire_event(self, event):
        if self._event_handler:
            try:
                getattr(self._event_handler, event)()
            except AttributeError:
                pass

    def write(self, data, callback=None):
        if not self._stream:
            self.connect()
            if not self._stream:
                raise ConnectionError('Tried to write to '
                                      'non-existent connection')

        if callback:
            _callback = lambda: callback(None)
            self.read_callbacks.append(_callback)
            cb = partial(self.read_callback, _callback)
        else:
            cb = None
        try:
            self._stream.write(data, callback=cb)
        except IOError, e:
            self.disconnect()
            raise ConnectionError(e.message)

    def read(self, length, callback=None):
        try:
            if not self._stream:
                self.disconnect()
                raise ConnectionError('Tried to read from '
                                      'non-existent connection')
            self.read_callbacks.append(callback)
            self._stream.read_bytes(length,
                                    callback=partial(self.read_callback,
                                                     callback))
        except IOError:
            self.fire_event('on_disconnect')

    def read_callback(self, callback, *args, **kwargs):
        self.read_callbacks.remove(callback)
        callback(*args, **kwargs)

    def readline(self, callback=None):
        try:
            if not self._stream:
                self.disconnect()
                raise ConnectionError('Tried to read from '
                                      'non-existent connection')
            self.read_callbacks.append(callback)
            self._stream.read_until('\r\n',
                                    callback=partial(self.read_callback,
                                                     callback))
        except IOError:
            self.fire_event('on_disconnect')

    def connected(self):
        if self._stream:
            return True
        return False


class ConnectionPool(object):
    '''
    'A Redis server connection pool.

    Arguments:
        max_connections - a maximum number of simultaneous
                          connections to a Redis Server,
        wait_for_available - do not raise an exceptionbut wait for a next
                             available connection if a connection limit
                             has been reached.
        **connection_kwargs
    '''
    def __init__(self, max_connections=None, wait_for_available=False,
                 **connection_kwargs):
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections or 2048
        self.wait_for_avaliable = wait_for_available
        self._created_connections = 0
        self._available_connections = deque()
        self._in_use_connections = set()
        self._waiting_clients = deque()

    def get_connection(self, event_handler=None):
        "Get a connection from the pool"
        try:
            connection = self._available_connections.pop()
        except IndexError:
            connection = self.make_connection()
        if connection:
            connection.set_event_handler(event_handler)
            self._in_use_connections.add(connection)
        elif self.wait_for_avaliable:
            connection = ConnectionStub(event_handler=event_handler)
            self._waiting_clients.append(connection)
        else:
            raise ConnectionError("Too many connections")
        return connection

    def make_connection(self):
        "Create a new connection"
        if self._created_connections >= self.max_connections:
            return None
        self._created_connections += 1
        return Connection(**self.connection_kwargs)

    def release(self, connection):
        "Releases the connection back to the pool"
        if isinstance(connection, ConnectionStub):
            self._waiting_clients.remove(connection)
            connection = connection.connection
            if not connection:
                return
        connection.set_event_handler(None)
        if self._waiting_clients:
            waiting = self._waiting_clients.pop()
            waiting.assign_connection(connection)
        else:
            if connection in self._in_use_connections:
                self._in_use_connections.remove(connection)
            self._available_connections.append(connection)

    def disconnect(self):
        "Disconnects all connections in the pool"
        all_conns = chain(self._available_connections,
                          self._in_use_connections)
        for connection in all_conns:
            connection.disconnect()


class ConnectionStub(object):
    '''
    A stub object to replace a client's connection until one is available.
    '''
    def __init__(self, event_handler=None):
        super(ConnectionStub)
        self.connection = None
        self.client = event_handler
        self.ready_callbacks = []

    def __getattribute__(self, name):
        try:
            return super(ConnectionStub, self).__getattribute__(name)
        except AttributeError:
            return getattr(object.__getattribute__(self, "connection"), name)

    def connected(self):
        if self.connection:
            return self.connection.connected()
        else:
            return True

    def ready(self):
        if self.connection:
            return self.connection.ready()
        else:
            return False

    def wait_until_ready(self, callback=None):
        if not self.connection:
            if callback:
                self.ready_callbacks.append(callback)
            return self
        else:
            return self.connection.wait_until_ready(callback=callback)

    def assign_connection(self, connection):
        self.connection = connection
        if self.ready_callbacks:
            connection.ready_callbacks += self.ready_callbacks
            self.ready_callbacks = []
            connection.set_event_handler(self.client)
            self.client.connection = connection
            self.client = None
            connection.continue_pending()
