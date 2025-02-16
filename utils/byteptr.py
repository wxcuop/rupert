import weakref
import ctypes

class BytePtr:
    """ High-performance managed byte buffer similar to C++ CharPtr """

    __slots__ = ("_buffer", "_view", "_own_memory", "_weak_ref")

    def __init__(self, data=None, own_memory=True):
        if data is None:
            self._buffer = bytearray()
        elif isinstance(data, (bytes, bytearray, memoryview)):
            self._buffer = bytearray(data) if own_memory else data
        else:
            raise TypeError("BytePtr only accepts bytes, bytearray, or memoryview.")

        self._view = memoryview(self._buffer)
        self._own_memory = own_memory
        self._weak_ref = None if own_memory else weakref.ref(self._buffer)

    @classmethod
    def strong_reference(cls, data):
        """ Creates an owned buffer (deep copy) """
        return cls(data, own_memory=True)

    @classmethod
    def weak_reference(cls, data):
        """ Creates a non-owned buffer (zero-copy reference) """
        return cls(data, own_memory=False)

    def get(self):
        """ Returns the raw byte buffer """
        return self._buffer if self._own_memory else self._weak_ref()

    def view(self):
        """ Returns a memoryview for zero-copy operations """
        return self._view

    def to_ctypes(self):
        """ Returns a ctypes pointer for interoperability with C libraries """
        return ctypes.cast(ctypes.pointer(ctypes.create_string_buffer(self._buffer)), ctypes.POINTER(ctypes.c_char))

    def resize(self, new_size):
        """ Resize buffer (only if owned) """
        if not self._own_memory:
            raise RuntimeError("Cannot resize a weak reference buffer")
        self._buffer.extend([0] * (new_size - len(self._buffer)))
        self._view = memoryview(self._buffer)

    def __len__(self):
        return len(self._buffer)

    def __del__(self):
        if self._own_memory:
            del self._buffer  # Free memory


class ByteBuffer:
    """ High-performance wrapper over BytePtr with a defined length """

    __slots__ = ("ptr", "length")

    def __init__(self, byte_ptr, length=None):
        if not isinstance(byte_ptr, BytePtr):
            raise TypeError("ByteBuffer requires a BytePtr instance")
        self.ptr = byte_ptr
        self.length = length if length is not None else len(byte_ptr)

    def get_data(self):
        """ Returns bytes data within buffer range """
        return self.ptr.view()[:self.length]

    def to_ctypes(self):
        """ Returns a ctypes-compatible pointer for C API usage """
        return self.ptr.to_ctypes()

    def __len__(self):
        return self.length
