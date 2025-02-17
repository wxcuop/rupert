import threading

class AtomicInt:
    def __init__(self, initial=0):
        self.value = initial
        self._lock = threading.Lock()

    def add_and_get(self, amount):
        with self._lock:
            self.value += amount
            return self.value

    def val_compare_and_swap(self, expect, new):
        with self._lock:
            if self.value == expect:
                self.value = new
            return self.value

class ThreadID:
    UNDEF = 0
    highest_thread_id = AtomicInt(0)

    def __init__(self, value=None):
        if value is None:
            self.thread_id = self.get_self_thread_id()
        else:
            self.thread_id = value

    def get_self_thread_id(self):
        if not hasattr(threading.local(), 'my_thread_id'):
            threading.local().my_thread_id = ThreadID.highest_thread_id.add_and_get(1)
        return threading.local().my_thread_id

    def claim(self):
        my_thread_id = self.get_self_thread_id()
        if self.thread_id != self.UNDEF:
            return self.thread_id == my_thread_id
        prev = self.thread_id
        if prev == self.UNDEF:
            self.thread_id = my_thread_id
        return prev == self.UNDEF

    def __int__(self):
        return self.thread_id

    def __eq__(self, other):
        return self.thread_id == other.thread_id

    def __del__(self):
        pass

# Example usage
if __name__ == "__main__":
    thread_id1 = ThreadID()
    print(int(thread_id1))  # Print the thread ID
    thread_id2 = ThreadID()
    print(int(thread_id2))  # Print the thread ID
    print(thread_id1.claim())  # Claim the thread ID
