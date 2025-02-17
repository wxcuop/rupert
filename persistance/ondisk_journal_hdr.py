class OnDiskJournalHdr:
    def __init__(self):
        self.creation_timestamp = Timestamp()
        self.highest_strm_num = 0
        self.highest_vec_num_plus_1 = 0
        self.strm_infos = [None] * LockFreeJournal.MAX_STRMS
        self.vec_infos = [None] * LockFreeJournal.MAX_VECS
        self.flags = 0

    def get_creation_timestamp(self):
        return self.creation_timestamp

    def get_highest_strm_num(self):
        return self.highest_strm_num

    def get_highest_committed_strm_num(self):
        for strm_num in range(self.highest_strm_num, -1, -1):
            if self.strm_infos[strm_num].committed_len > 0 and self.strm_infos[strm_num].strm_type != StrmType.UNKNOWN_STREAM:
                return strm_num
        return 0

    def get_highest_vec_num(self):
        return self.highest_vec_num_plus_1 - 1 if self.highest_vec_num_plus_1 > 0 else 0

    def get_highest_committed_vec_num(self):
        vec_num = self.get_highest_vec_num()
        for vec_num in range(vec_num, -1, -1):
            if self.vec_infos[vec_num].hop_one_slices[0].get_flag():
                return vec_num
        return 0

    def reinit(self, tx_strm):
        self.highest_strm_num = 0
        self.highest_vec_num_plus_1 = 0
        self.strm_infos = [None] * LockFreeJournal.MAX_STRMS
        self.vec_infos = [None] * LockFreeJournal.MAX_VECS

    def set_dir_not_exist_before_first_open(self, set_or_clear):
        if set_or_clear:
            self.flags |= LockFreeJournal.NOT_EXIST_BEFORE_OPEN_MASK
        else:
            self.flags &= LockFreeJournal.CLEAR_NOT_EXIST_BEFORE_OPEN_MASK

    def get_dir_not_exist_before_first_open(self):
        return bool(self.flags & LockFreeJournal.NOT_EXIST_BEFORE_OPEN_MASK)
