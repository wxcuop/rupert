import time
from threading import Lock

class Conflator:
    """
    A rate-limiting utility that triggers processing when:
    1. A specified time interval has elapsed.
    2. A specified number of events have occurred.

    Useful for throttling high-frequency event streams like market data processing.
    """

    def __init__(self, interval_seconds: float, event_threshold: int):
        """
        Initializes the Conflator.

        :param interval_seconds: Time interval threshold in seconds.
        :param event_threshold: Number of events threshold.
        """
        self.interval = interval_seconds
        self.event_threshold = event_threshold
        self.last_report_time = time.time()
        self.event_count = 0
        self.lock = Lock()  # Ensures thread safety

    def reset(self):
        """Resets the conflation timer and event counter."""
        self.last_report_time = time.time()
        self.event_count = 0

    def set_interval(self, interval_seconds: float):
        """Dynamically updates the time interval threshold."""
        self.interval = interval_seconds

    def set_event_threshold(self, event_threshold: int):
        """Dynamically updates the event count threshold."""
        self.event_threshold = event_threshold

    def outside_conflation_interval(self) -> bool:
        """Checks if enough time has passed since the last processing."""
        return (time.time() - self.last_report_time) > self.interval

    def reach_event_threshold(self) -> bool:
        """Increments event count and checks if it meets the threshold."""
        self.event_count += 1
        return self.event_count >= self.event_threshold

    def mark_event(self) -> bool:
        """
        Marks an event and determines if processing should be triggered.

        :return: True if processing should be triggered, False otherwise.
        """
        with self.lock:  # Ensure thread safety in multi-threaded environments
            if self.outside_conflation_interval() or self.reach_event_threshold():
                self.reset()
                return True
            return False

# Example Usage
if __name__ == "__main__":
    conflator = Conflator(interval_seconds=1, event_threshold=100)

    while True:
        time.sleep(0.01)  # Simulating incoming events
        if conflator.mark_event():
            print(f"Processing batch at {time.time()}")
