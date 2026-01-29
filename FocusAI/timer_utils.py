import time

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.is_running = False
        self.paused_time = None

    def start(self):
        self.is_running = True
        self.start_time = time.time()

    def pause(self):
        if self.is_running:
            self.paused_time = time.time()
            self.is_running = False

    def resume(self):
        if not self.is_running and self.paused_time:

            pause_duration = time.time() - self.paused_time
            self.start_time += pause_duration
            self.is_running = True

    def stop(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0