import ctypes
from typing import Dict, Any, Iterator, Tuple, Optional
import logging

class Configuration:
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def begin(self) -> Iterator[Tuple[str, Any]]:
        return iter(self.data.items())

    def end(self) -> Iterator[Tuple[str, Any]]:
        return iter([])

    def get_value(self, key: str, default: Optional[str] = None) -> str:
        return str(self.data.get(key, default))

def print_configuration(pt: Configuration) -> None:
    for key, value in pt.begin():
        logging.debug(f"{key}: {value.get_value('')}")
        print_configuration(Configuration(value))

def print_config(level: int, os: Any, config: Configuration) -> None:
    for key, value in config.begin():
        os.write(' ' * level)
        os.write(f"{key}: {value.get_value('')}\n")
        print_config(level + 1, os, Configuration(value))

def configuration_to_stream(os: Any, config: Configuration) -> None:
    print_config(1, os, config)

def dump_buffer(os: Any, buffer: bytes) -> None:
    dump_buffer_range(os, buffer, 0, len(buffer))

def dump_buffer_range(os: Any, buffer: bytes, begin: int, end: int) -> None:
    if begin is None:
        return

    os.write(buffer[begin:end].decode())

class RupUtil:

    @staticmethod
    def print_str(buf: ctypes.Array, buf_end: int, s: str) -> Tuple[ctypes.Array, int]:
        str_len = len(s)
        if buf + str_len <= buf_end:
            buf[:str_len] = s.encode()
            buf += str_len
        else:
            buf += str_len  # Update buf even if there's not enough space.
        return buf, buf_end

    @staticmethod
    def print_int64(buf: ctypes.Array, buf_end: int, val: int) -> Tuple[ctypes.Array, int]:
        if val < 0:
            if val == -9223372036854775808:
                return JisuUtil.print_str(buf, buf_end, "-9223372036854775808")
            val = -val
            buf, buf_end = JisuUtil.print_str(buf, buf_end, "-")
        
        if val < 10:
            if buf < buf_end:
                buf[0] = ord('0') + val
            buf += 1
        else:
            temp_buf = []
            while val != 0:
                temp_buf.append(ord('0') + (val % 10))
                val //= 10
            
            n = len(temp_buf)
            if buf + n <= buf_end:
                for char in reversed(temp_buf):
                    buf[0] = char
                    buf += 1
            else:
                buf += n
        
        return buf, buf_end

    @staticmethod
    def print_uint64(buf: ctypes.Array, buf_end: int, val: int) -> Tuple[ctypes.Array, int]:
        if val < 10:
            if buf < buf_end:
                buf[0] = ord('0') + val
            buf += 1
        else:
            temp_buf = []
            while val != 0:
                temp_buf.append(ord('0') + (val % 10))
                val //= 10
            
            n = len(temp_buf)
            if buf + n <= buf_end:
                for char in reversed(temp_buf):
                    buf[0] = char
                    buf += 1
            else:
                buf += n
        
        return buf, buf_end

    @staticmethod
    def print_double(buf: ctypes.Array, buf_end: int, val: float, prec: int) -> Tuple[ctypes.Array, int]:
        buf_len = max(buf_end - buf, 0)
        formatted_str = f"{val:.{prec}f}"
        num_bytes_required = len(formatted_str.encode())
        buf[:num_bytes_required] = formatted_str.encode()
        buf += num_bytes_required
        return buf, buf_end

    @staticmethod
    def print_double_without_trailing_zeros(buf: ctypes.Array, buf_end: int, val: float, prec: int) -> Tuple[ctypes.Array, int]:
        buf_len = max(buf_end - buf, 0)
        formatted_str = f"{val:.{prec}f}".rstrip('0').rstrip('.')
        num_bytes_required = len(formatted_str.encode())
        buf[:num_bytes_required] = formatted_str.encode()
        buf += num_bytes_required
        return buf, buf_end

    @staticmethod
    def round_nearest(number: float, modulo: int) -> int:
        return modulo * round(number / modulo)


# Example usage
if __name__ == "__main__":
    import io

    config_data = {
        "key1": {"subkey1": "value1", "subkey2": "value2"},
        "key2": {"subkey3": "value3"}
    }
    config = Configuration(config_data)

    # Example usage of print_configuration
    print_configuration(config)

    # Example usage of configuration_to_stream
    output_stream = io.StringIO()
    configuration_to_stream(output_stream, config)
    print(output_stream.getvalue())

    # Example usage of dump_buffer
    buf = b"Hello, World!"
    output_stream = io.StringIO()
    dump_buffer(output_stream, buf)
    print(output_stream.getvalue())

    # Example usage of JisuUtil
    buf = (ctypes.c_char * 100)()
    buf_end = 100

    buf, buf_end = JisuUtil.print_str(buf, buf_end, "Hello, World!")
    print(buf.value)

    buf, buf_end = JisuUtil.print_int64(buf, buf_end, -123456789)
    print(buf.value)

    buf, buf_end = JisuUtil.print_uint64(buf, buf_end, 123456789)
    print(buf.value)

    buf, buf_end = JisuUtil.print_double(buf, buf_end, 123.456, 2)
    print(buf.value)

    buf, buf_end = JisuUtil.print_double_without_trailing_zeros(buf, buf_end, 123.456, 2)
    print(buf.value)

    print(RupUtil.round_nearest(123.456, 10))
