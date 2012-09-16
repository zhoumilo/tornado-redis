import socket
from functools import partial
import weakref
from collections import deque

from tornado.iostream import IOStream

from .exceptions import ConnectionError


class Connection(object):
    def __init__(self, host, port, event_handler,
                 stop_after=None, io_loop=None):
        self.host = host
        self.port = port
        self._event_handler = weakref.proxy(event_handler)
        self.timeout = stop_after
        self._stream = None
        self._io_loop = io_loop

        self.in_progress = False
        self.read_callbacks = []
        self.ready_callbacks = deque()

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.check_ready_queue()

    def ready(self):
        return not self.read_callbacks and not self.ready_callbacks

    def wait_until_ready(self, callback=None):
        if callback:
            if not self.ready():
                self.ready_callbacks.append(callback)
            else:
                callback()
        return self

    def check_ready_queue(self):
        """
        Continue with pending command execution if all read operations are completed.
        """
        if not self.read_callbacks and self.ready_callbacks:
            # Pop a SINGLE callback from the queue and execute it.
            # The next one will be executed from the code
            # invoked by the callback
            callback = self.ready_callbacks.popleft()
            callback()

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

    def write(self, data):
        if not self._stream:
            self.connect()
            if not self._stream:
                raise ConnectionError('Tried to write to '
                                      'non-existent connection')

        try:
            self._stream.write(data)
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
