from time import sleep


class Checkout:
    def __init__(self, parent, event, lock):
        self.parent = parent
        self.event = event
        self.lock = lock

    def check_queue(self, primary, secundary):
        frame_id = None
        with self.lock:
            while not secundary.empty():
                frame_id, frame = secundary.get_nowait()
                primary.append((frame_id, frame))

    def check_error(self):
        if self.parent.poll():
            value = self.parent.recv()
            if isinstance(value, tuple):
                erro, exc_info = value
                print(exc_info)
                raise erro

    def fill_buffer(self, start_frame, last_frame, mapping):
        if start_frame <= last_frame and not self.event.is_set():
            self.parent.send(True)
            self.event.set()
            self.parent.send((start_frame, last_frame, mapping))
            # sleep(0.01)
