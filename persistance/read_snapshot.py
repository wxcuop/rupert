class ReadSnapshot:
    def __init__(self, lock_free_journal):
        self.lock_free_journal = lock_free_journal
        self.last_known_highest_strm_num = 0
        self.last_known_highest_vec_num = 0
        self.read_strm_infos = []
        self.read_vec_infos = []

    def do_snapshot(self):
        new_highest_strm_num = self.lock_free_journal.on_disk_journal_hdr.get_highest_committed_strm_num()
        new_highest_vec_num = self.lock_free_journal.on_disk_journal_hdr.get_highest_committed_vec_num()

        for vec_num in range(new_highest_vec_num + 1):
            read_vec_info = self.read_vec_infos[vec_num]
            if not read_vec_info.is_discovered:
                vec_num_plus_1 = self.lock_free_journal.on_disk_journal_hdr.vec_infos[vec_num].vec_num_plus_1
                if vec_num_plus_1 != 0:
                    vec = self.lock_free_journal.get_vec(vec_num)
                    vec.init(self.lock_free_journal, vec_num, vec.lock_free_journal.on_disk_journal_hdr.vec_infos[vec_num].vec_type, vec.lock_free_journal.on_disk_journal_hdr.vec_infos[vec_num].name, __PRETTY_FUNCTION__, True)
                    read_vec_info.is_discovered = True

            vec = self.lock_free_journal.vecs[vec_num]
            if vec and read_vec_info.is_discovered:
                read_vec_info.last_known_vec_idx = vec.get_max_item_idx() - 1

        for strm_num in range(new_highest_strm_num + 1):
            read_strm_info = self.read_strm_infos[strm_num]
            if not read_strm_info.is_discovered:
                strm_num_plus_1 = self.lock_free_journal.on_disk_journal_hdr.strm_infos[strm_num].strm_num_plus_1
                if strm_num_plus_1 != 0:
                    strm = self.lock_free_journal.get_strm(strm_num)
                    strm.init(self.lock_free_journal, strm_num, strm.lock_free_journal.on_disk_journal_hdr.strm_infos[strm_num].name, strm.lock_free_journal.on_disk_journal_hdr.strm_infos[strm_num].strm_type, __PRETTY_FUNCTION__, True)
                    read_strm_info.is_discovered = True

            strm = self.lock_free_journal.strms[strm_num]
            if strm and read_strm_info.is_discovered:
                read_strm_info.last_known_strm_len = strm.get_committed_len()

    def scan_vec_up_to_timestamp(self, vec_num, timestamp, strm_committed_lengths, previous_strm_offsets):
        read_vec_info = self.read_vec_infos[vec_num]
        if not read_vec_info.is_discovered:
            return 0

        total = 0
        vec = self.lock_free_journal.get_vec(vec_num)
        for idx in range(read_vec_info.last_read_vec_idx + 1, read_vec_info.last_known_vec_idx + 1):
            ts = vec.get_vec_item_timestamp(idx).get_milliseconds()
            pos = vec.get_vec_item_pos(idx)
            strm_off = pos.get_strm_off()
            if ts == 0:
                strm_off = previous_strm_offsets[pos.get_strm_num()]
            if (ts > 0 and ts >= timestamp) or strm_off > strm_committed_lengths[pos.get_strm_num()]:
                break
            previous_strm_offsets[pos.get_strm_num()] = strm_off
            total += 1

        read_vec_info.last_read_vec_idx += total
        return total
