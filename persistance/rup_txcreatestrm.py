class TxCreateStrm(Tx):
    def __init__(self, lfj):
        super().__init__(lfj.get_strm0())
        self.lfj = lfj

    def execute(self, new_strm_name, strm_type, caller):
        tx_strm = self.tx_strm
        lfj = self.lfj
        new_strm_num = lfj.alloc_next_strm_num(caller)
        new_strm = lfj.strms.get_or_create_elem(new_strm_num)

        with tx_strm.strm_write_mutex:
            new_strm.init(lfj, new_strm_num, new_strm_name, strm_type, caller, False)
            self.setup(caller)
            op_create_strm = LockFreeJournal.Tx.OpCreateStrm.init(self, new_strm_num, new_strm_name, strm_type, caller)
            self.set_tx_len_and_update_valid_len()
            op_create_strm.execute(lfj, self.tx_hdr_pos, caller)

    def execute_with_suffix(self, strm_name_suffix, strm_dir, strm_type, caller):
        strm_name = self.generate_strm_name(strm_name_suffix, strm_dir)
        self.execute(strm_name, strm_type, caller)
