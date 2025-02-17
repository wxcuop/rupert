import threading

class Semaphore:
    """
    A simple semaphore counter class that allows unrestricted increments
    but ensures decrements do not make the counter negative (blocking if necessary).
    """
    
    class ScopedLock:
        """ Context manager for automatic semaphore acquisition and release. """
        def __init__(self, semaphore):
            self.semaphore = semaphore
        
        def __enter__(self):
            self.semaphore.wait()
        
        def __exit__(self, exc_type, exc_value, traceback):
            self.semaphore.post()
    
    def __init__(self, initial_count=0):
        """
        Initialize the semaphore with an optional initial count.
        
        :param initial_count: Initial semaphore value (default: 0)
        """
        self._semaphore = threading.Semaphore(initial_count)
    
    def post(self, count=1):
        """
        Increment the semaphore count.
        
        :param count: Number of times to increment the semaphore.
        """
        for _ in range(count):
            self._semaphore.release()
    
    def wait(self):
        """
        Decrement the semaphore count, blocking if necessary.
        """
        self._semaphore.acquire()
    
    def try_wait(self):
        """
        Attempt to decrement the semaphore count without blocking.
        
        :return: True if the decrement was successful, False otherwise.
        """
        return self._semaphore.acquire(blocking=False)
