import time
from collections import deque
from threading import Lock

class TrafficMeter:
    INVALID_SLICE_INDEX = -1
    SLICE_SIZE_MS = 20

    def __init__(self, trailing_interval_seconds):
        self.trailing_interval_ms = trailing_interval_seconds * 1000
        self.slice_counters = deque([0] * (self.trailing_interval_ms // self.SLICE_SIZE_MS))
        self.current_slice_index = 0
        self.current_virtual_slice_index = 0
        self.current_slice_traffic = 0
        self.trailing_traffic = 0
        self.lock = Lock()

    def update_traffic(self, ts, amount=1):
        ts_ms = int(ts * 1000)
        return self._update_traffic(ts_ms, amount)

    def _update_traffic(self, ts_ms, amount=1):
        with self.lock:
            slice_index = ts_ms // self.SLICE_SIZE_MS
            if slice_index != self.current_virtual_slice_index:
                self._clear_slices(slice_index - self.current_virtual_slice_index)
                self.current_virtual_slice_index = slice_index
                self.current_slice_index = slice_index % len(self.slice_counters)

            self.slice_counters[self.current_slice_index] += amount
            self.trailing_traffic += amount
            return self.trailing_traffic

    def get_traffic_for_trailing_interval(self, ts=None):
        if ts is None:
            ts_ms = int(time.time() * 1000)
        else:
            ts_ms = int(ts * 1000)
        return self._get_traffic_for_trailing_interval(ts_ms)

    def _get_traffic_for_trailing_interval(self, ts_ms):
        with self.lock:
            self._update_traffic(ts_ms, 0)
            return self.trailing_traffic

    def _clear_slices(self, slices_to_clear):
        for _ in range(slices_to_clear):
            self.trailing_traffic -= self.slice_counters[self.current_slice_index]
            self.slice_counters[self.current_slice_index] = 0
            self.current_slice_index = (self.current_slice_index + 1) % len(self.slice_counters)

    def get_trailing_interval_seconds(self):
        return self.trailing_interval_ms // 1000

# Example usage
if __name__ == "__main__":
    meter = TrafficMeter(60)  # 60 seconds trailing interval
    meter.update_traffic(time.time(), 1)
    print(meter.get_traffic_for_trailing_interval())
