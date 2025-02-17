class SafeLeftShift:
    @staticmethod
    def shift(value: int, shift: int) -> int:
        """
        Safely left shift a given value by `shift` number of bits.
        If `shift` <= 63, perform the shift. Otherwise, return 0.
        
        :param value: The integer value to shift.
        :param shift: The number of bits to shift.
        :return: The shifted value or 0 if shift > 63.
        """
        return value << shift if shift <= 63 else 0

# Example Usage:
result = SafeLeftShift.shift(5, 3)  # Equivalent to 5 << 3
print(result)  # Output: 40

result = SafeLeftShift.shift(5, 64)  # Shift too large
print(result)  # Output: 0
