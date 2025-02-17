import os
import mmap
import struct
import threading
import fcntl
import errno
from collections import defaultdict
from typing import Callable, List, Tuple, Dict, Optional, Any

VAL_TO_NAME = lambda name: str(name)

# Constants
MAX_STRM_NAME_LEN = 127
MAX_VEC_NAME_LEN = 127
MAX_ENCODE_NAME_LEN = 127
MAX_COMP_ID_LEN = 63
MAX_SESSION_ID_LEN = 63
SEG_SIZE_SHIFT = 22
SEG_SIZE = 1 << SEG_SIZE_SHIFT
SEG_SIZE_MASK = SEG_SIZE - 1

class StrmType:
    UNKNOWN_STREAM = 0
    DATA_STREAM = 1
    TX_STREAM = 2
    TX_DATA_STREAM = 3

class VecType:
    UNKNOWN_VEC = 0
    MSG_VEC = 1
    ORDER_VEC = 2
    AUX_VEC = 3

class AuxTagsStatus:
    AuxTagsReady = 0
    AuxTagsNotReady = 1
    AuxTagsError = 2
    AuxTagsNone = 3

StrmTypeName = [
    "UNKNOWN_STREAM",
    "DATA_STREAM",
    "TX_STREAM",
    "TX_DATA_STREAM"
]

VecTypeName = [
    "UNKNOWN_VEC",
    "MSG_VEC",
    "ORDER_VEC",
    "AUX_VEC"
]

BufProcessor = Callable[[bytes, int], None]
PrinterFinder = Callable[[str, str], Callable[[str, bytes, int, int], None]]

class LFJObserver:
    pass

class AtomicUint32:
    def __init__(self, value=0):
        self.value = value
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            return self.value

    def set(self, value):
        with self.lock:
            self.value = value

class AtomicUint64:
    def __init__(self, value=0):
        self.value = value
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            return self.value

    def set(self, value):
        with self.lock:
            self.value = value

class LockFreeJournal:
    PRINT_NONE = 0
    PRINT_LITTLE = 1
    PRINT_MORE = 2
    PRINT_ALL = 3

    STRM_NUM_MASK = 0x000003ff
    MAX_STRMS = STRM_NUM_MASK
    MAX_STRM_NUM = MAX_STRMS - 1
    SEG_NUM_MASK = 0x00003fff
    MAX_SEGS = SEG_NUM_MASK
    MAX_SEG_NUM = MAX_SEGS - 1
    MAX_VECS = 1024
    MAX_VEC_NUM = MAX_VECS - 1
    STRM_OFF_MASK = ((1 << (32 + SEG_SIZE_SHIFT)) - 1)
    LFJ_STRM_0_NAME = "LFJ_STRM_0"
    TX_STRM_NAME_PREFIX = "TX_STRM"

    UNITIALIZED_STRM_NUM = MAX_STRMS
    UNITIALIZED_SEG_NUM = MAX_SEGS
    UNITIALIZED_VEC_NUM = MAX_VECS

    def __init__(self):
        self.strms = []
        self.vecs = []
        self.listeners = []

    class Pos:
        SEG_OFF_SHIFT = 0
        SEG_OFF_MASK = LockFreeJournal.SEG_SIZE_MASK
        SEG_NUM_SHIFT = SEG_OFF_SHIFT + 14
        SEG_NUM_MASK = LockFreeJournal.SEG_NUM_MASK
        STRM_OFF_SHIFT = 0
        STRM_OFF_MASK = LockFreeJournal.STRM_OFF_MASK
        STRM_NUM_SHIFT = STRM_OFF_SHIFT + 36
        STRM_NUM_MASK = LockFreeJournal.STRM_NUM_MASK
        LEN_SHIFT = STRM_NUM_SHIFT + 10
        LEN_MASK = 0x0001ffff
        FLAG_SHIFT = 63
        FLAG_MASK = 0x01

        def __init__(self):
            self.strm_num_seg_num_seg_off = 0

        def get_strm_num(self) -> int:
            return (self.strm_num_seg_num_seg_off >> self.STRM_NUM_SHIFT) & self.STRM_NUM_MASK

        def get_strm_off(self) -> int:
            return (self.strm_num_seg_num_seg_off >> self.STRM_OFF_SHIFT) & self.STRM_OFF_MASK

        def get_seg_num(self) -> int:
            return (self.strm_num_seg_num_seg_off >> self.SEG_NUM_SHIFT) & self.SEG_NUM_MASK

        def get_seg_off(self) -> int:
            return (self.strm_num_seg_num_seg_off >> self.SEG_OFF_SHIFT) & self.SEG_OFF_MASK

        def get_len(self) -> int:
            return (self.strm_num_seg_num_seg_off >> self.LEN_SHIFT) & self.LEN_MASK

        def get_flag(self) -> bool:
            return (self.strm_num_seg_num_seg_off >> self.FLAG_SHIFT) & self.FLAG_MASK

        def is_null(self) -> bool:
            return self.strm_num_seg_num_seg_off == 0

        def is_patch(self) -> bool:
            return self.get_flag()

        def __eq__(self, other):
            if isinstance(other, LockFreeJournal.Pos):
                return self.strm_num_seg_num_seg_off == other.strm_num_seg_num_seg_off
            return False

        def __ne__(self, other):
            return not self.__eq__(other)

        def __lt__(self, other):
            if isinstance(other, LockFreeJournal.Pos):
                return self.strm_num_seg_num_seg_off < other.strm_num_seg_num_seg_off
            return False

        def __gt__(self, other):
            return not self.__lt__(other) and not self.__eq__(other)

        def __le__(self, other):
            return self.__lt__(other) or self.__eq__(other)

        def __ge__(self, other):
            return not self.__lt__(other)

        def __repr__(self):
            return f"Pos({self.strm_num_seg_num_seg_off})"

        @staticmethod
        def get_max_len() -> int:
            return LockFreeJournal.Pos.LEN_MASK

    class Seg:
        def __init__(self):
            self.lock_free_journal = None
            self.strm = None
            self.seg_num_plus_1 = 0
            self.seg_data = None

        def get_seg_num(self) -> int:
            return self.seg_num_plus_1 - 1

        def get_strm(self):
            return self.strm

        def get_seg_data(self):
            return self.seg_data

        def init(self, strm, seg_data, seg_num, caller):
            if seg_data is None:
                raise Exception(f"Seg::init(): seg_data should not be None; strm_name={strm.get_strm_name()}, seg_num={seg_num}, caller={caller}")

            if self != strm.segs[seg_num]:
                raise Exception(f"Seg::init(): self should be equal to strm.segs[seg_num]; strm_name={strm.get_strm_name()}, seg_num={seg_num}, caller={caller}")

            self.lock_free_journal = strm.lock_free_journal
            self.strm = strm
            self.seg_data = seg_data
            self.seg_num_plus_1 = seg_num + 1

    class Strm:
        def __init__(self):
            self.lock_free_journal = None
            self.on_disk_strm_info = None
            self.strm_path = None
            self.owner_thread_id = threading.get_ident()
            self.fd_plus_1 = 0
            self.strm_num_plus_1 = 0
            self.strm_type = StrmType.UNKNOWN_STREAM
            self.last_known_file_size = 0
            self.segs = []
            self.alloc_heap_buf = None
            self.alloc_buf = None
            self.alloc_buf_strm_off = 0
            self.strm_write_mutex = threading.RLock()

        def get_strm_num(self) -> int:
            return self.strm_num_plus_1 - 1

        def get_strm_name(self) -> str:
            return self.strm_path  # Assuming the path is the name

        def get_strm_path(self) -> str:
            return self.strm_path

        def get_strm_fd(self) -> int:
            return self.fd_plus_1 - 1

        def get_committed_len(self) -> int:
            return self.on_disk_strm_info.committed_len.get()

        def get_valid_len(self) -> int:
            return self.on_disk_strm_info.valid_len.get()

        def get_alloc_len(self) -> int:
            return self.on_disk_strm_info.alloc_len.get()

        def is_tx_strm(self) -> bool:
            return self.strm_type == StrmType.TX_STREAM

        def get_strm_type(self) -> int:
            return self.strm_type

        def is_initialized(self) -> bool:
            return self.lock_free_journal is not None

        def locate_data_in_strm(self, strm_off: int, caller: str) -> bytes:
            seg_num = self.get_seg_num(strm_off)
            seg_off = self.get_seg_off(strm_off)
            seg_data = self.map_seg(seg_num, True, caller)
            return seg_data[seg_off:]

        def map_seg(self, seg_num: int, create_if_needed: bool, caller: str) -> bytes:
            while len(self.segs) <= seg_num:
                self.segs.append(None)

            seg = self.segs[seg_num]
            if seg is None or seg.seg_data is None:
                seg = LockFreeJournal.Seg()
                seg_data = self.map_seg_(seg_num, create_if_needed, caller, False)
                seg.init(self, seg_data, seg_num, caller)
                self.segs[seg_num] = seg
            return seg.seg_data

        def map_seg_(self, seg_num: int, create_if_needed: bool, caller: str, is_recovery: bool) -> bytes:
            # Implementation of map_seg_ function
            pass

        def acquire_write_lock(self, fd, file_name):
            file_lock = struct.pack('hhllhh', mmap.LOCK_EX, 0, 0, 0, 0, 0)
            try:
                fcntl.fcntl(fd, fcntl.F_SETLK, file_lock)
            except IOError as e:
                if e.errno in [errno.EACCES, errno.EAGAIN]:
                    fcntl.fcntl(fd, fcntl.F_GETLK, file_lock)
                    raise Exception(f"Cannot acquire write lock on {file_name}; file is currently locked by pid {file_lock.l_pid}")
                else:
                    raise Exception(f"Cannot acquire write lock on {file_name}; errno={errno} {os.strerror(errno)}")

        def create_strm_file(self, strm_path: str) -> int:
            flags = os.O_RDWR if self.lock_free_journal.is_writeable else os.O_RDONLY
            fd = os.open(strm_path, flags, 0)
            mode = 0

            if fd >= 0:
                os.close(fd)
                if self.lock_free_journal.is_writeable:
                    mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH
                    flags |= os.O_TRUNC | os.O_CREAT
                    fd = os.open(strm_path, flags, mode)
            elif errno == errno.ENOENT and self.lock_free_journal.is_writeable:
                mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH
                flags |= os.O_CREAT
                fd = os.open(strm_path, flags, mode)

            if fd == -1:
                raise Exception(f"::open() failed; strm_path={strm_path}")

            if self.lock_free_journal.is_writeable:
                self.acquire_write_lock(fd, strm_path)

            return fd

        def recover_strm_from_file(self, strm_num: int, strm_path: str) -> int:
            if not self.lock_free_journal.did_exist_before_open:
                raise Exception(f"Cannot recover a strm when lfj did not exist before open; strm_path={strm_path}")

            flags = os.O_RDWR if self.lock_free_journal.is_writeable else os.O_RDONLY
            fd = os.open(strm_path, flags, 0)

            if fd < 0:
                raise Exception(f"strm file does not exist; strm_path={strm_path}")

            if self.lock_free_journal.is_writeable:
                self.acquire_write_lock(fd, strm_path)

            return fd

        def buf_malloc(self, size: int, caller: str) -> bytes:
            self.buf_free(self.alloc_heap_buf if self.alloc_heap_buf else self.alloc_buf, caller)
            return self.buf_compact_and_realloc(0, size, caller)

        def buf_free(self, alloc_buf: bytes, caller: str):
            if self.alloc_heap_buf:
                if alloc_buf != self.alloc_heap_buf:
                    raise Exception(f"alloc_buf specified != alloc_heap_buf_; caller={caller}")
                del self.alloc_heap_buf
                self.alloc_heap_buf = None
            else:
                if alloc_buf != self.alloc_buf:
                    raise Exception(f"alloc_buf specified != alloc_buf_; caller={caller}")

            self.alloc_buf = None
            self.alloc_buf_strm_off = 0

        def buf_compact_and_realloc(self, num_bytes_to_compact_at_front: int, new_buf_len: int, caller: str) -> bytes:
            committed_len = self.get_committed_len()
            alloc_len = self.get_alloc_len()

            if self.alloc_buf is None:
                self.alloc_buf_strm_off = committed_len
                self.alloc_buf = self.map_seg(self.get_seg_num(committed_len), True, caller) + self.get_seg_off(committed_len)
                self.alloc_heap_buf = None

            num_bytes_committed = committed_len - self.alloc_buf_strm_off
            old_buf_len = alloc_len - self.alloc_buf_strm_off
            new_alloc_buf_strm_off = self.alloc_buf_strm_off + num_bytes_to_compact_at_front

            if num_bytes_to_compact_at_front > num_bytes_committed:
                raise Exception(f"num_bytes_to_compact_at_front exceeds num_bytes_committed; caller={caller}")

            if num_bytes_committed > old_buf_len:
                raise Exception(f"num_bytes_committed should not exceed old_buf_len; caller={caller}")

            if num_bytes_committed >= num_bytes_to_compact_at_front + new_buf_len:
                raise Exception(f"new buf should contain space after committed_len_; caller={caller}")

            num_new_segs = self.additional_new_segs_needed(new_alloc_buf_strm_off, new_buf_len)
            if num_new_segs > 1:
                raise Exception(f"Adding new_buf_len to committed_len would span 2 or more segs; caller={caller}")

            num_bytes_at_front_of_new_buf = num_bytes_committed - num_bytes_to_compact_at_front
            self.alloc_buf_strm_off = new_alloc_buf_strm_off
            self.on_disk_strm_info.alloc_len.set(new_alloc_buf_strm_off + new_buf_len)

            if self.alloc_heap_buf is None:
                if num_bytes_to_compact_at_front > 0:
                    self.alloc_buf += num_bytes_to_compact_at_front

                if num_new_segs == 0:
                    return self.alloc_buf

                self.alloc_heap_buf = bytearray(new_buf_len)
                if num_bytes_at_front_of_new_buf > 0:
                    self.alloc_heap_buf[:num_bytes_at_front_of_new_buf] = self.alloc_buf[:num_bytes_at_front_of_new_buf]
                self.alloc_buf = self.alloc_heap_buf
                return self.alloc_buf

            if num_new_segs == 0:
                self.alloc_heap_buf = None
                seg_num = self.get_seg_num(new_alloc_buf_strm_off)
                seg_data = self.map_seg(seg_num, True, caller)
                self.alloc_buf = seg_data + self.get_seg_off(new_alloc_buf_strm_off)
            else:
                new_heap_buf = bytearray(new_buf_len)
                if num_bytes_at_front_of_new_buf > 0:
                    new_heap_buf[:num_bytes_at_front_of_new_buf] = self.alloc_heap_buf[num_bytes_to_compact_at_front:num_bytes_to_compact_at_front + num_bytes_at_front_of_new_buf]
                del self.alloc_heap_buf
                self.alloc_heap_buf = new_heap_buf
                self.alloc_buf = self.alloc_heap_buf

            return self.alloc_buf

        def additional_new_segs_needed(self, new_alloc_buf_strm_off: int, new_buf_len: int) -> int:
            # Implementation of additional_new_segs_needed function
            pass

        def buf_commit(self, num_bytes_to_commit: int, caller: str) -> 'LockFreeJournal.Pos':
            old_committed_len = self.get_committed_len()
            alloc_len = self.get_alloc_len()
            alloc_buf_strm_off = self.alloc_buf_strm_off
            num_bytes_committed = old_committed_len - alloc_buf_strm_off
            buf_len = alloc_len - alloc_buf_strm_off
            new_committed_len = old_committed_len + num_bytes_to_commit

            if self.on_disk_strm_info is None:
                raise Exception(f"on_disk_strm_info should not be null; caller={caller}")

            if self.alloc_heap_buf:
                start_pos = old_committed_len
                num_bytes_to_copy = num_bytes_to_commit
                cur_pos = start_pos

                while num_bytes_to_copy > 0:
                    seg_num = self.get_seg_num(cur_pos)
                    seg_off = self.get_seg_off(cur_pos)
                    seg_data = self.map_seg(seg_num, True, caller)
                    if seg_data is None:
                        raise Exception(f"map_seg() returns null; caller={caller}")

                    n = SEG_SIZE - seg_off
                    if n > num_bytes_to_copy:
                        n = num_bytes_to_copy
                    seg_data[seg_off:seg_off + n] = self.alloc_heap_buf[num_bytes_committed + num_bytes_to_commit - num_bytes_to_copy:num_bytes_committed + num_bytes_to_commit - num_bytes_to_copy + n]
                    num_bytes_to_copy -= n
                    cur_pos += n

            self.on_disk_strm_info.valid_len.set(new_committed_len)
            self.on_disk_strm_info.committed_len.set(new_committed_len)
            return self.Pos(self.get_strm_num(), old_committed_len, 0)

        def process_committed_data(self, buf_processor: BufProcessor):
            committed_len = self.get_committed_len()
            if committed_len == 0:
                return

            strm_fd = self.get_strm_fd()
            committed_data = mmap.mmap(strm_fd, committed_len, access=mmap.ACCESS_READ)

            try:
                buf_processor(committed_data, committed_len)
            finally:
                committed_data.close()

        def get_data_by_iovec(self, begin_off: int, end_off: int) -> List[mmap.mmap]:
            if end_off < begin_off:
                raise Exception(f"end_off should not be less than begin_off; begin_off={begin_off}, end_off={end_off}")

            iov = []
            cur_off = begin_off

            while cur_off < end_off:
                seg_num = self.get_seg_num(cur_off)
                seg_off = self.get_seg_off(cur_off)

                seg_data = self.map_seg(seg_num, True, __PRETTY_FUNCTION__)
                if seg_data is None:
                    raise Exception(f"seg_data should not be null; seg_num={seg_num}, seg_off={seg_off}")

                if seg_num == self.get_seg_num(end_off):
                    iov.append(seg_data[seg_off:end_off - cur_off])
                    cur_off = end_off
                else:
                    iov.append(seg_data[seg_off:SEG_SIZE])
                    cur_off += SEG_SIZE - seg_off

            return iov

        def init(self, lock_free_journal, strm_num, strm_name, strm_type, caller, is_recovery):
            if strm_name is None or len(strm_name) > MAX_STRM_NAME_LEN:
                raise Exception(f"strm_name should not be null or longer than {MAX_STRM_NAME_LEN} characters; strm_name={strm_name}, caller={caller}")

            if self.lock_free_journal is not None or self.on_disk_strm_info is not None or self.is_initialized():
                raise Exception(f"Strm is already initialized; strm_name={strm_name}, caller={caller}")

            self.lock_free_journal = lock_free_journal
            self.on_disk_strm_info = None
            self.strm_num_plus_1 = strm_num + 1
            self.strm_name = strm_name
            self.strm_type = strm_type
            self.last_known_file_size = 0
            self.strm_path = f"{lock_free_journal.lfj_name}/{strm_name}"
            self.strm_write_mutex = threading.RLock()

            if is_recovery:
                self.fd_plus_1 = lock_free_journal.recover_strm_from_file(strm_num, self.strm_path) + 1
                self.map_seg_(0, True, __PRETTY_FUNCTION__, True)
                if self.on_disk_strm_info.valid_len < self.on_disk_strm_info.committed_len:
                    raise Exception(f"Strm valid len {self.on_disk_strm_info.valid_len} is less than committed len {self.on_disk_strm_info.committed_len}")

                valid_seg_num = self.get_seg_num(self.on_disk_strm_info.valid_len)
                for seg_num in range(1, valid_seg_num + 1):
                    self.map_seg_(seg_num, True, __PRETTY_FUNCTION__, True)

                if lock_free_journal.is_writeable:
                    if lock_free_journal.is_rollbackable:
                        if self.on_disk_strm_info.strm_type == StrmType.DATA_STREAM:
                            self.on_disk_strm_info.valid_len = self.on_disk_strm_info.committed_len
                            self.on_disk_strm_info.alloc_len = self.on_disk_strm_info.committed_len
                        elif self.on_disk_strm_info.strm_type == StrmType.TX_STREAM:
                            if self.on_disk_strm_info.valid_len > self.on_disk_strm_info.committed_len:
                                self.rollback_tx(self.on_disk_strm_info.committed_len, self.on_disk_strm_info.valid_len)
                                self.on_disk_strm_info.committed_len = self.on_disk_strm_info.valid_len
                                after_valid_data = self.locate_data_in_strm(self.on_disk_strm_info.valid_len, __PRETTY_FUNCTION__)
                                seg_end = self.locate_data_in_strm(self.get_seg_num(self.on_disk_strm_info.valid_len), 0, __PRETTY_FUNCTION__) + SEG_SIZE
                                after_valid_data[:seg_end - after_valid_data] = b'\x00' * (seg_end - after_valid_data)
                    else:
                        pass
            else:
                self.map_seg_(0, True, __PRETTY_FUNCTION__, False)

        def refresh_from_file(self, is_committed_len):
            if self.on_disk_strm_info is None:
                raise Exception("the stream is not initialized")

            length = self.get_committed_len() if is_committed_len else self.get_valid_len()
            seg_num = self.get_seg_num(length)
            seg_off = self.get_seg_off(length)

            if seg_off == 0 and seg_num > 0:
                seg_num -= 1

            for i in range(seg_num + 1):
                self.map_seg_(i, False, __PRETTY_FUNCTION__, False)

    def open(self, lfj_name, is_writeable, is_rollbackable):
        if lfj_name is None or len(lfj_name) == 0:
            raise Exception("lfj_name should not be null or of 0-length")

        if self.lfj_name is not None or self.is_initialized:
            raise Exception("lfj object is already initialized")

        self.lfj_name = lfj_name
        self.is_writeable = is_writeable
        self.is_rollbackable = is_rollbackable

        dir_exists = os.path.exists(lfj_name)
        did_exist_before_open = False

        if dir_exists:
            strm_path0 = os.path.join(lfj_name, self.LFJ_STRM_0_NAME)
            fd0 = os.open(strm_path0, os.O_RDONLY) if os.path.exists(strm_path0) else -1
            if fd0 > 0:
                did_exist_before_open = True
            elif not is_writeable:
                return None
            os.close(fd0)
        elif is_writeable:
            os.makedirs(lfj_name)
            dir_exists = True

        if not dir_exists:
            return None

        self.dir_did_exist_before_open = dir_exists
        self.did_exist_before_open = did_exist_before_open

        try:
            if is_writeable and not did_exist_before_open:
                strm0 = self.Strm()
                strm0.init(self, 0, self.LFJ_STRM_0_NAME, StrmType.TX_STREAM, __PRETTY_FUNCTION__, False)

            self.update_cache(did_exist_before_open)
            self.is_initialized = True
        except Exception as ex:
            self.close()
            raise ex

        return self

    def update_cache(self, did_exist_before_open):
        if did_exist_before_open:
            strm0 = self.strms[0]
            strm0.init(self, 0, self.LFJ_STRM_0_NAME, StrmType.TX_STREAM, __PRETTY_FUNCTION__, True)

            for strm_num in range(1, self.on_disk_journal_hdr.get_highest_committed_strm_num() + 1):
                strm_info = self.on_disk_journal_hdr.strm_infos[strm_num]
                if strm_info.strm_num_plus_1 != 0:
                    strm = self.Strm()
                    strm.init(self, strm_num, strm_info.name, strm_info.strm_type, __PRETTY_FUNCTION__, True)

            for vec_num in range(self.on_disk_journal_hdr.get_highest_committed_vec_num() + 1):
                vec_info = self.on_disk_journal_hdr.vec_infos[vec_num]
                if vec_info.vec_num_plus_1 != 0:
                    vec = self.Vec()
                    vec.init(self, vec_num, vec_info.vec_type, vec_info.name, __PRETTY_FUNCTION__, True)

    def close(self):
        if not self.is_initialized:
            return
        self.is_initialized = False

        for strm in self.strms:
            if strm is None:
                continue
            for seg in strm.segs:
                if seg is None:
                    continue
                if seg.seg_data is not None:
                    seg.seg_data.close()
                    seg.seg_data = None
                seg.lock_free_journal = None
                seg.seg_num_plus_1 = 0

            strm.lock_free_journal = None
            strm.on_disk_strm_info = None
            if strm.fd_plus_1 != 0:
                os.close(strm.fd_plus_1 - 1)
                strm.fd_plus_1 = 0

        self.is_writeable = False
        self.is_rollbackable = False

        if self.lfj_dir:
            self.lfj_dir.close()
            self.lfj_dir = None

        if self.lfj_name:
            self.lfj_name = None

        self.on_disk_journal_hdr = None

    def get_strm(self, strm_num):
        if strm_num >= len(self.strms):
            return None
        return self.strms[strm_num]

    def get_vec(self, vec_num):
        if vec_num >= len(self.vecs):
            return None
        return self.vecs[vec_num]

    def locate_data_by_pos(self, pos, data_1, msg_len_1, data_2, msg_len_2):
        # Implementation of locate_data_by_pos function
        pass

    def locate_order_data_from_tx_hdr(self, cur_pos, next_pos):
        # Implementation of locate_order_data_from_tx_hdr function
        pass

    def locate_order_data_by_pos(self, cur_pos, next_pos):
        # Implementation of locate_order_data_by_pos function
        pass

    def rollback_tx(self, committed_len, valid_len):
        # Implementation of rollback_tx function
        pass

    def alloc_next_strm_num(self, caller):
        # Implementation of alloc_next_strm_num function
        pass

    def alloc_next_vec_num(self, caller):
        # Implementation of alloc_next_vec_num function
        pass

    def get_transaction_latency(self, item, vec_direction):
        # Implementation of get_transaction_latency function
        pass

    def add_listener(self, listener):
        self.listeners.append(listener)

    def notify_listeners(self, event_type, *args):
        for listener in self.listeners:
            listener(event_type, *args)
          
