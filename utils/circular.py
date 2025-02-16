import queue
import threading
import functools
import time


class CircularQueue:
    """A lock-free circular buffer for single-producer, single-consumer use cases."""

    def __init__(self, capacity, callback, throttle=None):
        """
        Initializes the circular queue.

        Args:
            capacity (int): Maximum number of items in the queue (must be a power of 2).
            callback (callable): Function to process items.
            throttle (callable, optional): Function to throttle processing. Defaults to None.
        """
        if capacity & (capacity - 1) != 0:
            raise ValueError("Capacity must be a power of 2")

        self.capacity = capacity
        self.queue = queue.Queue(capacity)
        self.callback = callback
        self.throttle = throttle or (lambda: None)
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)

    def start(self):
        """Starts the consumer thread."""
        self.thread.start()

    def stop(self):
        """Stops the consumer thread and waits for it to finish."""
        self.stop_event.set()
        self.thread.join()

    def push(self, item, block=True, timeout=None):
        """
        Adds an item to the queue.

        Args:
            item: The item to add.
            block (bool): Whether to block if the queue is full. Defaults to True.
            timeout (float, optional): Time to wait before giving up. Defaults to None.

        Returns:
            bool: True if the item was added, False otherwise.
        """
        try:
            self.queue.put(item, block=block, timeout=timeout)
            return True
        except queue.Full:
            return False

    def _worker(self):
        """Internal method to process queue items."""
        while not self.stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.1)  # Avoid busy waiting
                self.throttle()
                self.callback(item)
            except queue.Empty:
                continue


# Example Usage
if __name__ == "__main__":
    def process_item(item):
        print(f"Processing: {item}")

    def throttle():
        time.sleep(0.1)  # Simulating throttling

    queue = CircularQueue(capacity=8, callback=process_item, throttle=throttle)
    queue.start()

    for i in range(20):
        if queue.push(i, block=False):
            print(f"Added: {i}")
        else:
            print(f"Queue full, dropping: {i}")
        time.sleep(0.05)  # Simulate producer speed

    time.sleep(2)  # Let the queue process items
    queue.stop()
