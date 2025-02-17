import time
from collections import deque
from threading import Lock
import logging

class TrafficMeter:
    INVALID_SLICE_INDEX = -1
    SLICE_SIZE_MS = 20

    def __init__(self, trailing_interval_seconds):
        self.trailing_interval_ms = trailing_interval_seconds * 1000
        self.slice_counters = deque([0] * (self.trailing_interval_ms // self.SLICE_SIZE_MS))
        self.current_slice_index = TrafficMeter.INVALID_SLICE_INDEX
        self.current_virtual_slice_index = 0
        self.current_slice_traffic = 0
        self.trailing_traffic = 0
        self.lock = Lock()

    def update_traffic(self, ts_ms, amount=1):
        new_slice_index = (ts_ms % self.trailing_interval_ms) // self.SLICE_SIZE_MS
        new_virtual_slice_index = ts_ms // self.trailing_interval_ms * len(self.slice_counters) + new_slice_index

        with self.lock:
            if new_slice_index == self.current_slice_index and new_virtual_slice_index == self.current_virtual_slice_index:
                self.current_slice_traffic += amount
            else:
                if self.current_slice_index != TrafficMeter.INVALID_SLICE_INDEX:
                    if new_virtual_slice_index < self.current_virtual_slice_index:
                        logging.error("Timestamp out of order!")
                        self.validate_slice_counters()
                        return self.trailing_traffic
                    elif new_virtual_slice_index - self.current_virtual_slice_index > len(self.slice_counters):
                        self.slice_counters = deque([0] * len(self.slice_counters))
                        self.trailing_traffic = 0
                    else:
                        nos_slices = (new_slice_index - self.current_slice_index) if new_slice_index > self.current_slice_index else (len(self.slice_counters) + new_slice_index - self.current_slice_index)
                        self.clear_slices(self.current_slice_index, nos_slices)

                    self.trailing_traffic += (self.current_slice_traffic - self.slice_counters[self.current_slice_index])
                    self.slice_counters[self.current_slice_index] = self.current_slice_traffic

                self.current_slice_index = new_slice_index
                self.current_virtual_slice_index = new_virtual_slice_index
                self.current_slice_traffic = amount

            self.validate_slice_counters()
            return self.trailing_traffic

    def clear_slices(self, last_valid_slice, nos_slices):
        nos = min(nos_slices, len(self.slice_counters))
        for i in range(1, nos + 1):
            slice_index = (i + last_valid_slice) % len(self.slice_counters)
            self.trailing_traffic -= self.slice_counters[slice_index]
            self.slice_counters[slice_index] = 0

    def validate_slice_counters(self):
        slice_counters_sum = sum(self.slice_counters)
        assert slice_counters_sum == self.trailing_traffic

    def get_traffic_for_trailing_interval(self, ts=None):
        if ts is None:
            ts_ms = int(time.time() * 1000)
        else:
            ts_ms = int(ts * 1000)
        return self._get_traffic_for_trailing_interval(ts_ms)

    def _get_traffic_for_trailing_interval(self, ts_ms):
        with self.lock:
            self.update_traffic(ts_ms, 0)
            return self.trailing_traffic

    def get_trailing_interval_seconds(self):
        return self.trailing_interval_ms // 1000

    @staticmethod
    def test():
        m1 = TrafficMeter(1)
        assert len(m1.slice_counters) == 50
        traffic = m1.update_traffic(1)
        assert traffic == 1
        traffic = m1.update_traffic(2)
        assert traffic == 2
        traffic = m1.update_traffic(9)
        assert traffic == 3
        traffic = m1.update_traffic(99)
        assert traffic == 4
        traffic = m1.update_traffic(100)
        assert m1.current_slice_index == 5
        assert traffic == 1
        traffic = m1.update_traffic(300)
        assert traffic == 6
        traffic = m1.update_traffic(350)
        assert traffic == 7
        traffic = m1.update_traffic(399)
        assert traffic == 8
        assert m1.current_slice_index == 19
        traffic = m1.update_traffic(450, 0)
        assert traffic == 8
        traffic = m1.update_traffic(650)
        assert traffic == 9
        assert m1.current_slice_index == 32
        traffic = m1.update_traffic(950)
        assert traffic == 10
        assert m1.current_slice_index == 47

        m2 = TrafficMeter(5)
        assert m2.update_traffic(2 * 500, 2) == 2
        assert m2.update_traffic(2 * 500, -1) == 1
        assert m2.update_traffic(2 * 500 + 200) == 2

# Example usage
if __name__ == "__main__":
    meter = TrafficMeter(60)  # 60 seconds trailing interval
    meter.update_traffic(int(time.time() * 1000), 1)
    print(meter.update_traffic(int(time.time() * 1000)))
    TrafficMeter.test()
