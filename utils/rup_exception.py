import traceback


class RupException(Exception):
    """
    Custom exception class that wraps an error number and an explanation text.
    Includes file name and line number where the exception was raised.
    """

    def __init__(self, errnum, message=None, filename=None, linenum=None, format_string=None, *args):
        """
        Initialize the exception.

        :param errnum: Error number (int)
        :param message: Explanation text (str)
        :param filename: File name where the exception occurred (optional)
        :param linenum: Line number where the exception occurred (optional)
        :param format_string: Format string for additional details (optional)
        :param args: Arguments to format into the format string
        """
        self.errnum = errnum
        self.filename = filename
        self.linenum = linenum

        # If a format string is provided, format it with the arguments
        if format_string:
            formatted_message = format_string % args if args else format_string
            if filename and linenum:
                self.message = f"{filename}:{linenum}: {formatted_message}"
            else:
                self.message = formatted_message
        elif message:
            self.message = message
        else:
            self.message = "An error occurred."

        super().__init__(self.message)

    def __str__(self):
        return f"Error {self.errnum}: {self.message}"


# Helper functions 
def create_exception_with_message(errnum, text):
    """
    Create a RupException with an error number and a plain message.

    :param errnum: Error number (int)
    :param text: Explanation text (str)
    :return: RupException instance
    """
    return RupException(errnum=errnum, message=text)


def create_exception_with_format(filename, linenum, errnum, format_string, *args):
    """
    Create a RupException with file/line information and a formatted message.

    :param filename: File name where the exception occurred (str)
    :param linenum: Line number where the exception occurred (int)
    :param errnum: Error number (int)
    :param format_string: Format string for additional details
    :param args: Arguments to format into the format string
    :return: RupException instance
    """
    return RupException(errnum=errnum, filename=filename, linenum=linenum,
                         format_string=format_string, *args)


# Example usage of the ported code
if __name__ == "__main__":
    try:
        # Example 1: Exception with a plain message
        raise create_exception_with_message(404, "Resource not found")
    except RupException as e:
        print(e)

    try:
        # Example 2: Exception with file/line info and formatted message
        raise create_exception_with_format("example.py", 42, 500,
                                           "Server error occurred: %s", "Internal issue")
    except RupException as e:
        print(e)
