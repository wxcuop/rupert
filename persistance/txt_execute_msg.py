class TxExecuteMsgs(Tx):
    def __init__(self, lfj):
        super().__init__(lfj.get_or_create_own_tx_strm())

    def set_vecs(self, *vecs):
        self.vecs = vecs

    def execute(self, *args, timestamp, caller):
        lfj = self.tx_strm.get_lfj()
        if not lfj:
            raise Exception(f"lfj is not set; caller={caller}")

        self.setup(caller)

        ops = []
        for i in range(0, len(args), 2):
            pos = args[i]
            seq_num = args[i + 1]
            vec = self.vecs[i // 2]
            vec_num = vec.get_vec_num()
            ops.append(LockFreeJournal.Tx.OpSetVecItem.init(self, vec_num, seq_num, pos, timestamp, __PRETTY_FUNCTION__))

        self.set_tx_len_and_update_valid_len()
        for op in ops:
            op.execute(lfj, self.tx_hdr_pos, __PRETTY_FUNCTION__)

        self.commit()
