import threading

class InvokeGuard:
    """
    A guard that ensures a given function is executed exactly once,
    either explicitly via invoke() or automatically upon destruction.
    
    While invoke_guard makes sense in C++ due to deterministic destruction and std::call_once, Python provides better alternatives:

    Use atexit for program-wide cleanup.
    Use context managers (with) for RAII-like behavior.
    Use threading.Event() for ensuring a function runs once.
    In most cases, you don’t need an invoke_guard in Python
    """

    def __init__(self, func):
        """
        :param func: A callable function to be executed once.
        """
        if not callable(func):
            raise TypeError("InvokeGuard requires a callable function")
        self._func = func
        self._executed = False
        self._lock = threading.Lock()

    def invoke(self):
        """
        Executes the function exactly once.
        """
        with self._lock:
            if not self._executed:
                self._func()
                self._executed = True

    def __del__(self):
        """
        Ensures the function is executed if not already called.
        """
        self.invoke()

# Example usage
if __name__ == "__main__":
    def cleanup():
        print("Cleanup function executed.")

    guard = InvokeGuard(cleanup)
    guard.invoke()  # Explicit call (optional)
    # If not called explicitly, it will be invoked when `guard` is deleted.
