class StringBuffer:
    def __init__(self, padding=' ', thousands_separator=False, precision=2, strip_trailing_zeroes=False):
        self.buffer = []
        self.padding = padding
        self.thousands_separator = thousands_separator
        self.precision = precision
        self.strip_trailing_zeroes = strip_trailing_zeroes

    def append(self, value):
        if isinstance(value, str):
            self.buffer.append(value)
        elif isinstance(value, int):
            self.buffer.append(str(value))
        elif isinstance(value, float):
            formatted_value = f"{value:.{self.precision}f}"
            if self.strip_trailing_zeroes:
                formatted_value = formatted_value.rstrip('0').rstrip('.')
            self.buffer.append(formatted_value)
        elif isinstance(value, bool):
            self.buffer.append("true" if value else "false")
        else:
            raise TypeError("Unsupported type for append")

    def __str__(self):
        return ''.join(self.buffer)

    def reset(self):
        self.buffer = []

    def set_precision(self, precision):
        self.precision = precision

    def set_padding(self, padding):
        self.padding = padding

    def set_thousands_separator(self, thousands_separator):
        self.thousands_separator = thousands_separator

    def set_strip_trailing_zeroes(self, strip_trailing_zeroes):
        self.strip_trailing_zeroes = strip_trailing_zeroes


# Helper functions
def to_string(value, precision=2):
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}".rstrip('0').rstrip('.')
    elif isinstance(value, bool):
        return "true" if value else "false"
    else:
        raise TypeError("Unsupported type for to_string")


# Example usage
sb = StringBuffer()
sb.append("Price Tolerance check failed, limit price ")
sb.append(12345.678)
sb.append(" is more than ")
sb.append(50)
sb.append("%, from the market ")
sb.append(12000.123)
sb.append('.')

print(str(sb))  # Output: Price Tolerance check failed, limit price 12345.68 is more than 50%, from the market 12000.12.
