    new_alloc_buf_strm_off, new_buf_len)
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
