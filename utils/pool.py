import threading
import queue

class MemoryPool:
    def __init__(self, object_type, init_alloc_size=32768, thread_safe=True):
        self.object_type = object_type
        self.init_alloc_size = init_alloc_size
        self.pool = queue.Queue()
        self.lock = threading.Lock() if thread_safe else None
        
        # Preallocate objects
        for _ in range(init_alloc_size):
            self.pool.put(object_type())
    
    def allocate(self):
        if self.lock:
            with self.lock:
                return self._get_object()
        return self._get_object()
    
    def deallocate(self, obj):
        if self.lock:
            with self.lock:
                self.pool.put(obj)
        else:
            self.pool.put(obj)
    
    def _get_object(self):
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            return self.object_type()

# Example usage
class MyObject:
    def __init__(self):
        self.data = None

# Create a thread-safe memory pool
pool = MemoryPool(MyObject, init_alloc_size=10, thread_safe=True)

obj = pool.allocate()
obj.data = "Example"

print(obj.data)  # Example

pool.deallocate(obj)
