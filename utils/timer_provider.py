import threading
import time
from collections import deque
from typing import Callable

TIMER_MAXWAIT_MSECS = 100

class TimerProvider:
    timer_id_t = int
    timer_fn_t = Callable[[timer_id_t, int], int]

    class Timer:
        def __init__(self):
            self.timer_id = 0
            self.callback = None
            self.interval = 0
            self.scheduled = 0
            self.canceled = False
            self.next = None

    class TimerMap:
        def __init__(self, timer_id, timer):
            self.timer_id = timer_id
            self.timer = timer
            self.next = None

    _instance = None
    start = time.time()

    def __init__(self):
        self.next_id = 0
        self.timer_map = None
        self.timer_map_lock = threading.Lock()
        self.timer_lock = threading.Lock()
        self.pending = None
        self.freelist = None
        self.active = False
        self.timers = None
        self.timer_thread = None

    @staticmethod
    def instance():
        if TimerProvider._instance is None:
            TimerProvider._instance = TimerProvider()
        return TimerProvider._instance

    def add_timer(self, next_interval, callback):
        with self.timer_lock:
            timer_id = self.next_id
            self.next_id += 1
            new_timer = self.Timer()
            new_timer.timer_id = timer_id
            new_timer.callback = callback
            new_timer.interval = next_interval
            new_timer.scheduled = int((time.time() - self.start) * 1e6) + next_interval
            self.pending = new_timer
        return timer_id

    def remove_timer(self, timer_id):
        with self.timer_lock:
            prev = None
            curr = self.timer_map
            while curr:
                if curr.timer_id == timer_id:
                    if prev:
                        prev.next = curr.next
                    else:
                        self.timer_map = curr.next
                    return True
                prev = curr
                curr = curr.next
        return False

    def __call__(self):
        while self.active:
            with self.timer_lock:
                now = int((time.time() - self.start) * 1e6)
                if self.pending:
                    self.timers = self.pending
                    self.pending = None
                curr = self.timers
                while curr:
                    if curr.scheduled <= now:
                        next_interval = curr.callback(curr.timer_id, curr.interval)
                        if next_interval == 0:
                            self.remove_timer(curr.timer_id)
                        else:
                            curr.scheduled = now + next_interval
                    curr = curr.next
            time.sleep(0.001)  # Sleep for 1ms

    def start(self):
        self.active = True
        self.timer_thread = threading.Thread(target=self)
        self.timer_thread.start()
        return self.timer_thread

    @staticmethod
    def get_ticks():
        return int((time.time() - TimerProvider.instance().start) * 1e6)

# Example usage
if __name__ == "__main__":
    def example_callback(timer_id, interval):
        print(f"Timer {timer_id} called with interval {interval}")
        return interval

    timer_provider = TimerProvider.instance()
    timer_provider.start()
    timer_id = timer_provider.add_timer(1000000, example_callback)  # 1 second
    time.sleep(2)
    timer_provider.remove_timer(timer_id)
