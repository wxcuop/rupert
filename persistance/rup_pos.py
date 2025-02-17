class Pos:
    SEG_OFF_SHIFT = 0
    SEG_OFF_MASK = LockFreeJournal.SEG_SIZE_MASK
    SEG_NUM_SHIFT = SEG_OFF_SHIFT + 14
    SEG_NUM_MASK = LockFreeJournal.SEG_NUM_MASK
    STRM_OFF_SHIFT = 0
    STRM_OFF_MASK = LockFreeJournal.STRM_OFF_MASK
    STRM_NUM_SHIFT = STRM_OFF_SHIFT + 36
    STRM_NUM_MASK = LockFreeJournal.STRM_NUM_MASK
    LEN_SHIFT = STRM_NUM_SHIFT + 10
    LEN_MASK = 0x0001ffff
    FLAG_SHIFT = 63
    FLAG_MASK = 0x01

    def __init__(self):
        self.strm_num_seg_num_seg_off = 0

    def get_strm_num(self) -> int:
        return (self.strm_num_seg_num_seg_off >> self.STRM_NUM_SHIFT) & self.STRM_NUM_MASK

    def get_strm_off(self) -> int:
        return (self.strm_num_seg_num_seg_off >> self.STRM_OFF_SHIFT) & self.STRM_OFF_MASK

    def get_seg_num(self) -> int:
        return (self.strm_num_seg_num_seg_off >> self.SEG_NUM_SHIFT) & self.SEG_NUM_MASK

    def get_seg_off(self) -> int:
        return (self.strm_num_seg_num_seg_off >> self.SEG_OFF_SHIFT) & self.SEG_OFF_MASK

    def get_len(self) -> int:
        return (self.strm_num_seg_num_seg_off >> self.LEN_SHIFT) & self.LEN_MASK

    def get_flag(self) -> bool:
        return (self.strm_num_seg_num_seg_off >> self.FLAG_SHIFT) & self.FLAG_MASK

    def is_null(self) -> bool:
        return self.strm_num_seg_num_seg_off == 0

    def is_patch(self) -> bool:
        return self.get_flag()

    def __eq__(self, other):
        if isinstance(other, Pos):
            return self.strm_num_seg_num_seg_off == other.strm_num_seg_num_seg_off
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Pos):
            return self.strm_num_seg_num_seg_off < other.strm_num_seg_num_seg_off
        return False

    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __repr__(self):
        return f"Pos({self.strm_num_seg_num_seg_off})"

    @staticmethod
    def get_max_len() -> int:
        return LockFreeJournal.Pos.LEN_MASK
