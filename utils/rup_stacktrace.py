import traceback
import inspect

def truncated(filepath):
    """Extracts the filename from a full file path."""
    return filepath.split('/')[-1]

def backtrace(indent=0):
    """
    Generates a formatted stack trace with indentation.
    """
    indentation = ' ' * indent
    stack = traceback.extract_stack()[:-1]  # Exclude the last call to this function
    formatted_trace = []

    for frame in stack:
        filename = truncated(frame.filename)
        function = frame.name
        line_number = frame.lineno
        formatted_trace.append(f"{indentation}{filename} : {function}() at line {line_number}")

    return "\n".join(formatted_trace)
