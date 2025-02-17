import os
import mmap
import struct
import threading
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
