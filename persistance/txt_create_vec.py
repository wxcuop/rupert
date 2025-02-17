class TxCreateVec(Tx):
    def __init__(self, lfj):
        super().__init__(lfj.get_strm0())
        self.lfj = lfj

    def execute(self, comp_id, session_id, vec_encode_name, vec_dir, vec_type, instance_id, caller, item_idx_base):
        new_vec_name = self.generate_vec_name(comp_id, vec_dir, instance_id)
        tx_strm = self.tx_strm
        lfj = self.lfj
        new_vec_num = lfj.alloc_next_vec_num(caller)
        with tx_strm.strm_write_mutex:
            self.setup(caller)
            op_create_vec = LockFreeJournal.Tx.OpCreateVec.init(self, new_vec_num, new_vec_name, vec_encode_name, comp_id, session_id, vec_dir, instance_id, item_idx_base, vec_type)
            self.set_tx_len_and_update_valid_len()
            op_create_vec.execute(lfj, self.tx_hdr_pos, caller)
            tx_create_strm = LockFreeJournal.TxCreateStrm(lfj)
            tx_create_strm.execute(new_vec_name, StrmType.TX_DATA_STREAM, caller)
            strm = lfj.get_strm(new_vec_name)
            self.setup(caller)
            op_set_vec_strm_num = LockFreeJournal.Tx.OpSetVecStrmNum.init(self, new_vec_num, strm.get_strm_num(), caller)
            self.set_tx_len_and_update_valid_len()
            op_set_vec_strm_num.execute(lfj, self.tx_hdr_pos, caller)
