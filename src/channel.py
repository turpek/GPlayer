from queue import Queue
from threading import Lock
import queue


class _Channel:
    def __init__(self, send, recv, send_err, recv_err):
        self._send = send
        self._recv = recv
        self._handle = True
        self._error = False
        self.closed = False
        self.send_err = send_err
        self.recv_err = recv_err
        self.lock = Lock()

    def _check_error(self):
        if not self.recv_err.empty():
            self._error = True
        if self._error is True:
            raise BrokenPipeError('Broken pipe')

    def _check_closed(self):
        if self._handle is None:
            raise OSError("handle is closed")

    def send(self, msg):
        self._check_closed()
        self._check_error()
        with self.lock:
            self._send.put_nowait(msg)

    def recv(self):
        self._check_closed()
        self._check_error()
        with self.lock:
            return self._recv.get()

    def poll(self):
        self._check_closed()
        with self.lock:
            return not self._recv.empty()

    def close(self):
        self._handle = None
        self.closed = True
        with self.lock:
            self.send_err.put(True)


class Channel:
    def __new__(self):
        inpt = Queue()
        outp = Queue()
        send_err = Queue()
        recv_err = Queue()

        self.pipe1 = _Channel(inpt, outp, send_err, recv_err)
        self.pipe2 = _Channel(outp, inpt, recv_err, send_err)
        return self.pipe1, self.pipe2
