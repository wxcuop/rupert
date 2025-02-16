import struct
import io
import typing
from typing import TypeVar, Generic, List, Set, Dict, Tuple, Union

T = TypeVar("T")


class Stream:
    """Base class for streams."""


class SizeStream(Stream):
    """Stream that tracks the size of written data without storing it."""

    def __init__(self):
        self._size = 0

    def write(self, data: bytes):
        """Track the size of written data."""
        self._size += len(data)

    def clear(self):
        """Reset size counter."""
        self._size = 0

    @property
    def size(self) -> int:
        """Return the total size."""
        return self._size


class DataStream(Stream):
    """Stream that writes and reads binary data."""

    def __init__(self, buffer: bytes = b""):
        self._buffer = io.BytesIO(buffer)

    def write(self, data: bytes):
        """Write bytes to stream."""
        self._buffer.write(data)

    def read(self, size: int) -> bytes:
        """Read bytes from stream."""
        return self._buffer.read(size)

    def reset(self):
        """Reset the stream position."""
        self._buffer.seek(0)

    def get_value(self) -> bytes:
        """Get the entire byte content."""
        return self._buffer.getvalue()


def serialize(stream: Stream, value: Union[bool, int, float, str, bytes, List, Set, Dict, Tuple]):
    """Serialize various types into the stream."""
    if isinstance(stream, SizeStream):
        if isinstance(value, bool):
            stream.write(b"\x00")  # 1 byte
        elif isinstance(value, int):
            stream.write(b"\x00\x00\x00\x00")  # Assuming 4-byte int
        elif isinstance(value, float):
            stream.write(b"\x00\x00\x00\x00\x00\x00\x00\x00")  # Assuming 8-byte float
        elif isinstance(value, str):
            stream.write(struct.pack("<I", len(value)))  # String length
            stream.write(value.encode("utf-8"))
        elif isinstance(value, bytes):
            stream.write(struct.pack("<I", len(value)))
            stream.write(value)
        elif isinstance(value, (list, set)):
            stream.write(struct.pack("<I", len(value)))  # Collection length
            for item in value:
                serialize(stream, item)
        elif isinstance(value, dict):
            stream.write(struct.pack("<I", len(value)))  # Dictionary size
            for key, val in value.items():
                serialize(stream, key)
                serialize(stream, val)
        elif isinstance(value, tuple):
            for item in value:
                serialize(stream, item)

    elif isinstance(stream, DataStream):
        if isinstance(value, bool):
            stream.write(struct.pack("<?", value))
        elif isinstance(value, int):
            stream.write(struct.pack("<i", value))
        elif isinstance(value, float):
            stream.write(struct.pack("<d", value))
        elif isinstance(value, str):
            encoded = value.encode("utf-8")
            stream.write(struct.pack("<I", len(encoded)))
            stream.write(encoded)
        elif isinstance(value, bytes):
            stream.write(struct.pack("<I", len(value)))
            stream.write(value)
        elif isinstance(value, (list, set)):
            stream.write(struct.pack("<I", len(value)))
            for item in value:
                serialize(stream, item)
        elif isinstance(value, dict):
            stream.write(struct.pack("<I", len(value)))
            for key, val in value.items():
                serialize(stream, key)
                serialize(stream, val)
        elif isinstance(value, tuple):
            for item in value:
                serialize(stream, item)


def deserialize(stream: DataStream, value_type: typing.Type[T]) -> T:
    """Deserialize various types from the stream."""
    if value_type == bool:
        return struct.unpack("<?", stream.read(1))[0]
    elif value_type == int:
        return struct.unpack("<i", stream.read(4))[0]
    elif value_type == float:
        return struct.unpack("<d", stream.read(8))[0]
    elif value_type == str:
        length = struct.unpack("<I", stream.read(4))[0]
        return stream.read(length).decode("utf-8")
    elif value_type == bytes:
        length = struct.unpack("<I", stream.read(4))[0]
        return stream.read(length)
    elif typing.get_origin(value_type) == list:
        length = struct.unpack("<I", stream.read(4))[0]
        item_type = typing.get_args(value_type)[0]
        return [deserialize(stream, item_type) for _ in range(length)]
    elif typing.get_origin(value_type) == set:
        length = struct.unpack("<I", stream.read(4))[0]
        item_type = typing.get_args(value_type)[0]
        return {deserialize(stream, item_type) for _ in range(length)}
    elif typing.get_origin(value_type) == dict:
        length = struct.unpack("<I", stream.read(4))[0]
        key_type, val_type = typing.get_args(value_type)
        return {deserialize(stream, key_type): deserialize(stream, val_type) for _ in range(length)}
    elif typing.get_origin(value_type) == tuple:
        item_types = typing.get_args(value_type)
        return tuple(deserialize(stream, t) for t in item_types)
    else:
        raise TypeError(f"Unsupported type: {value_type}")


# Example usage:

# Measuring size
size_stream = SizeStream()
serialize(size_stream, 42)
serialize(size_stream, "hello world")
serialize(size_stream, [1, 2, 3, 4])
print(f"Estimated size: {size_stream.size} bytes")

# Writing data
data_stream = DataStream()
serialize(data_stream, 42)
serialize(data_stream, "hello world")
serialize(data_stream, [1, 2, 3, 4])

# Reading data
data_stream.reset()
print(deserialize(data_stream, int))
print(deserialize(data_stream, str))
print(deserialize(data_stream, List[int]))
