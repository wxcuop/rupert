class TxPatchMsg(Tx):
    def __init__(self, lfj):
        super().__init__(lfj.get_or_create_own_tx_strm())

    def set_vec(self, vec):
        self.vec = vec

    def execute(self, seq_num, patch_len, timestamp, caller):
        lfj = self.tx_strm.get_lfj()
        if not lfj or not self.vec:
            raise Exception(f"vec is not set or lfj is not set; caller={caller}")

        self.setup(caller)
        op_patch_msg = LockFreeJournal.Tx.OpPatchMsg.init(self, self.vec.get_vec_num(), seq_num, patch_len, timestamp, __PRETTY_FUNCTION__)
        self.set_tx_len_and_update_valid_len()
        op_patch_msg.execute(lfj, self.tx_hdr_pos, __PRETTY_FUNCTION__)
        self.commit()
