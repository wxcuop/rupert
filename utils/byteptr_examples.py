from byteptr import BytePtr, ByteBuffer
import ctypes

# Example 1: Creating and Managing Buffers Efficiently
strong_buf = BytePtr.strong_reference(b"Hello, world!")
print(strong_buf.get())  # Output: b'Hello, world!'

# Create a weak reference (zero-copy)
weak_buf = BytePtr.weak_reference(strong_buf.get())
print(weak_buf.get())  # Output: b'Hello, world!'

# Example 2: Zero-Copy Processing using memoryview
view = strong_buf.view()
print(view[:5])  # Output: b'Hello'

# Example 3: Resizing a Buffer (Only for Strong References)
strong_buf.resize(20)  # Expands buffer with zero bytes
print(len(strong_buf))  # Output: 20

# Example 4: Using with C APIs via ctypes
ptr = strong_buf.to_ctypes()
c_func = ctypes.CDLL("libc.so.6").puts
c_func.argtypes = [ctypes.POINTER(ctypes.c_char)]
c_func(ptr)  # Should print "Hello, world!" (on Unix-like systems)

# Example 5: Wrapping Buffers with Length Constraints (ByteBuffer)
buf = ByteBuffer(strong_buf, length=5)
print(buf.get_data())  # Output: b'Hello'

# Example 6: Handling Large Binary Files Efficiently
with open("large_binary.dat", "rb") as f:
    file_data = f.read()
    file_buffer = BytePtr.weak_reference(file_data)

# Process chunks efficiently using memoryview
view = file_buffer.view()
chunk = view[:1024]  # Read first 1024 bytes
print(chunk)
