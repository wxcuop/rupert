class Vec:
    def __init__(self):
        self.lock_free_journal = None
        self.on_disk_vec_info = None

    def init(self, lock_free_journal, vec_num, vec_type, vec_name, caller, is_recovery):
        if vec_name is None or len(vec_name) > MAX_VEC_NAME_LEN:
            raise Exception(f"vec_name should not be null or longer than {MAX_VEC_NAME_LEN} characters; vec_name={vec_name}, caller={caller}")

        if self.lock_free_journal is not None or self.on_disk_vec_info is not None:
            raise Exception(f"Vec is already initialized; vec_name={vec_name}, caller={caller}")

        self.lock_free_journal = lock_free_journal
        self.on_disk_vec_info = lock_free_journal.on_disk_journal_hdr.vec_infos[vec_num] if is_recovery else None

    def get_vec_item(self, idx):
        # Implementation of get_vec_item function
        pass

    def get_item_data_by_idx(self, idx, data_1, len_1, data_2, len_2):
        # Implementation of get_item_data_by_idx function
        pass

    def get_vec_item_pos(self, idx):
        # Implementation of get_vec_item_pos function
        pass

    def get_vec_item_timestamp(self, idx):
        # Implementation of get_vec_item_timestamp function
        pass

    def is_aux_tags_committed(self, idx):
        if not self.on_disk_vec_info.is_vec_item_strm_committed(self.lock_free_journal, idx):
            return AuxTagsStatus.AuxTagsNotReady

        item = self.get_vec_item(idx)
        if item is None:
            return AuxTagsStatus.AuxTagsNotReady

        pos = item.pos
        aux_len_pos = pos.get_calibrated_pos(pos.get_len(), 4)
        strm = self.lock_free_journal.get_strm(aux_len_pos.get_strm_num())
        committed_strm_len = strm.get_committed_len()

        if aux_len_pos.get_strm_off() > committed_strm_len:
            return AuxTagsStatus.AuxTagsNotReady

        data_1, data_2 = None, None
        msg_len_1, msg_len_2 = 0, 0
        self.lock_free_journal.locate_data_by_pos(aux_len_pos, data_1, msg_len_1, data_2, msg_len_2)
        aux_len = self.get_uint32_from(data_1, msg_len_1, data_2, msg_len_2)

        if aux_len == 0:
            return AuxTagsStatus.AuxTagsNone
        if aux_len > self.Pos.LEN_MASK:
            return AuxTagsStatus.AuxTagsError
        if aux_len + aux_len_pos.get_strm_off() > committed_strm_len:
            return AuxTagsStatus.AuxTagsNotReady

        return AuxTagsStatus.AuxTagsReady

    def get_uint32_from(self, data_1, msg_len_1, data_2, msg_len_2):
        if msg_len_1 + msg_len_2 != 4:
            raise Exception("parse data length is greater than 4")
        if msg_len_2 == 0:
            return struct.unpack('I', data_1)[0]

        buf = data_1 + data_2
        return struct.unpack('I', buf)[0]
