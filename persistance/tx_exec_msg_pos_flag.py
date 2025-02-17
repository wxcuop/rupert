class TxExecuteMsgPosFlag(Tx):
    def __init__(self, lfj):
        super().__init__(lfj.get_or_create_own_tx_strm())

    def execute(self, seq_num, vec, caller):
        lfj = self.tx_strm.get_lfj()
        if not lfj or not vec:
            raise Exception(f"vec is null or lfj is not set; caller={caller}")

        self.setup(caller)
        op_set_pos_flag = LockFreeJournal.Tx.OpSetItemPosFlag.init(self, 1, vec.get_vec_num(), seq_num, __PRETTY_FUNCTION__)
        self.set_tx_len_and_update_valid_len()
        op_set_pos_flag.execute(lfj, self.tx_hdr_pos, __PRETTY_FUNCTION__)
        self.commit()
