from typing import List, Callable, TypeVar, Generic
from functools import partial

T = TypeVar('T')
V = TypeVar('V')

class Unpack(Generic[T, V]):
    result_t = List[T]
    reader_t = Callable[[result_t, V], None]

    @classmethod
    def unpack(cls, reader: reader_t, *args: V) -> result_t:
        u = cls(reader, *args)
        return u.result_

    def __init__(self, reader: reader_t, *args: V) -> None:
        self.result_ = []
        self.unpack_(reader, *args)

    def unpack_(self, reader: reader_t) -> None:
        pass

    def unpack_(self, reader: reader_t, x: V, *args: V) -> None:
        reader(self.result_, x)
        self.unpack_(reader, *args)


def unpack_config(config, *args: str) -> List[T]:
    def reader(v: List[T], str_: str) -> None:
        opt = config.get_optional(str_)
        if opt:
            v.append(opt)

    return Unpack[T, str].unpack(reader, *args)
