import os
import struct
import select

class EventFd:
    """
    EventFd is a Python wrapper for Linux's eventfd system call. It provides
    an event notification mechanism useful for inter-thread/process signaling.
    """
    def __init__(self, initval: int = 0, flags: int = 0):
        """
        Initialize the event file descriptor.

        :param initval: Initial counter value (default is 0).
        :param flags: Flags to modify behavior (e.g., os.EFD_NONBLOCK for non-blocking mode).
        """
        self.fd = os.eventfd(initval, flags)
    
    def write(self, val: int):
        """
        Increment the eventfd counter by writing a 64-bit unsigned integer.

        :param val: Value to increment the counter by.
        """
        os.write(self.fd, struct.pack("Q", val))
    
    def read(self) -> int:
        """
        Read the eventfd counter value. This blocks if no events are available.
        After reading, the counter is reset to 0 by the OS.

        :return: The value read from the eventfd counter.
        """
        return struct.unpack("Q", os.read(self.fd, 8))[0]
    
    def ready(self) -> bool:
        """
        Check if the eventfd has data available without blocking.

        :return: True if the eventfd is ready to read, False otherwise.
        """
        r, _, _ = select.select([self.fd], [], [], 0)
        return bool(r)
    
    def post(self):
        """
        Post an event by incrementing the eventfd counter by 1.
        Equivalent to signaling a semaphore.
        """
        self.write(1)
    
    def wait(self):
        """
        Wait for an event by reading the eventfd counter. This blocks until an event is available.
        """
        self.read()
    
    def fd(self) -> int:
        """
        Get the raw file descriptor of the eventfd.

        :return: The file descriptor.
        """
        return self.fd
    
    def __del__(self):
        """
        Destructor to close the file descriptor and release resources.
        """
        os.close(self.fd)

# Example usage
def main():
    efd = EventFd()
    efd.post()  # Signal event
    if efd.ready():
        print("Event is ready!")
    efd.wait()  # Wait for event
    print("Event consumed")

if __name__ == "__main__":
    main()
