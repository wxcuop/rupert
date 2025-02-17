import threading

class SpinLock:
    """
    A lightweight spinlock implementation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._flag = 0  # Simulating atomic flag

    def lock(self):
        """Acquires the lock, spinning until it becomes available."""
        while True:
            with self._lock:
                if self._flag == 0:
                    self._flag = 1
                    return

    def unlock(self):
        """Releases the lock."""
        with self._lock:
            self._flag = 0
