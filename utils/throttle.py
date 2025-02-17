import time
import logging
from collections import deque
from datetime import datetime, timedelta

class Throttle:
    class Item:
        def __init__(self, tv=None):
            if tv is None:
                self.tv = datetime.min
            else:
                self.tv = tv

        def __sub__(self, other):
            delta = self.tv - other.tv
            return delta.seconds * 1000000 + delta.microseconds

        @staticmethod
        def now():
            return Throttle.Item(datetime.now())

    def __init__(self, n, period_us):
        self.queue = deque(maxlen=n)
        self.period_us = period_us
        for _ in range(n):
            self.queue.append(self.Item())

    def spin_add(self):
        head = self.queue[0]
        first = True
        while True:
            item = self.Item.now()
            if item - head > self.period_us:
                self.queue.popleft()
                self.queue.append(item)
                return
            if first:
                logging.info(f"Throttling for {self.period_us - (item - head)}us")
                first = False

    def sleep_add(self):
        micros = self.try_add()
        if micros > 0:
            logging.info(f"Throttling for {micros}us")
            time.sleep(micros / 1000000.0)

    def try_add(self):
        head = self.queue[0]
        item = self.Item.now()
        diff = item - head
        if diff > self.period_us:
            self.queue.popleft()
            self.queue.append(item)
            return 0
        return self.period_us - diff

class SpinThrottle(Throttle):
    def __init__(self, n=1000):
        super().__init__(n, 1000000)

    def __call__(self):
        self.spin_add()

# Example usage
if __name__ == "__main__":
    throttle = SpinThrottle()
    throttle()
