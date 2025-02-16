class IncreaseOnlyBuffer:
    """
    A buffer that can only increase in size. 
    Useful for cases where memory needs to be reused without shrinking.
    """

    def __init__(self, min_size: int):
        """
        Initialize the buffer with a minimum size.
        
        :param min_size: The initial minimum size of the buffer.
        """
        self.min_size = min_size
        self.buffer = bytearray(min_size)

    def ensure_size(self, required_size: int = None) -> memoryview:
        """
        Ensure that the buffer is at least `required_size` bytes.
        If the buffer is smaller, it grows but never shrinks.

        :param required_size: The required size in bytes.
        :return: A memoryview to the buffer.
        """
        if required_size is None:
            required_size = self.min_size

        if len(self.buffer) < required_size:
            self.buffer.extend(bytearray(required_size - len(self.buffer)))

        return memoryview(self.buffer)

    def size(self) -> int:
        """
        Get the current size of the buffer.

        :return: The size of the buffer.
        """
        return len(self.buffer)
