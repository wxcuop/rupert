class Str:
    MAX_EMBEDDED_LEN = 15
    STR_EXTERNALLY_STORED = 0xFF
    digit_pairs = (
        "00010203040506070809"
        "10111213141516171819"
        "20212223242526272829"
        "30313233343536373839"
        "40414243444546474849"
        "50515253545556575859"
        "60616263646566676869"
        "70717273747576777879"
        "80818283848586878889"
        "90919293949596979899"
    )

    def __init__(self, value=""):
        if isinstance(value, int):
            self._set_from_int(value)
        elif isinstance(value, str):
            self._set(value)
        elif isinstance(value, Str):
            self._set(value.c_str())
        else:
            raise TypeError("Unsupported type for Str initialization")

    def _set(self, value):
        if len(value) <= self.MAX_EMBEDDED_LEN:
            self._embedded = value
            self._external = None
        else:
            self._embedded = None
            self._external = value

    def _set_from_int(self, number):
        self._set(str(number))

    def length(self):
        return len(self._external if self._external else self._embedded)

    def empty(self):
        return self.length() == 0

    def c_str(self):
        return self._external if self._external else self._embedded

    def __str__(self):
        return self.c_str()

    def __repr__(self):
        return f"Str('{self.c_str()}')"

    def __eq__(self, other):
        if isinstance(other, Str):
            return self.c_str() == other.c_str()
        elif isinstance(other, str):
            return self.c_str() == other
        return False

    def __lt__(self, other):
        if isinstance(other, (Str, str)):
            return self.c_str() < str(other)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, (Str, str)):
            return Str(self.c_str() + str(other))
        return NotImplemented

    def __getitem__(self, index):
        return self.c_str()[index]

    def reset(self):
        self._embedded = ""
        self._external = None

    def store_int_as_str(self, number):
        self._set_from_int(number)

    def to_std_string(self):
        return str(self)

    def __hash__(self):
        h = 0
        for char in self.c_str():
            h = 31 * h + ord(char)
        return h

    # Translated and integrated methods
    def is_embedded(self):
        return ord(self.chars_[self.MAX_EMBEDDED_LEN]) <= self.MAX_EMBEDDED_LEN

    def length(self):
        len = ord(self.chars_[self.MAX_EMBEDDED_LEN])
        if len <= self.MAX_EMBEDDED_LEN:
            if len == 0:
                return 0 if self.chars_[0] == '\0' else self.MAX_EMBEDDED_LEN
            return len
        return self.len_

    def c_str(self):
        return self.chars_ if self.is_embedded() else self.external_str_

    def to_str(self, ret_str_len):
        len = ord(self.chars_[self.MAX_EMBEDDED_LEN])
        if len <= self.MAX_EMBEDDED_LEN:
            if len == 0:
                ret_str_len = 0 if self.chars_[0] == '\0' else self.MAX_EMBEDDED_LEN
                return self.chars_
            ret_str_len = len
            return self.chars_
        ret_str_len = self.len_
        return self.external_str_

    def init(self, str):
        if str is None:
            self.init(str, 0)
        else:
            p = self.chars_
            p_end = p + self.MAX_EMBEDDED_LEN + 1
            s = str
            while s and p < p_end:
                p.append(s[0])
                s = s[1:]
            if p >= p_end:
                str_len = len(str)
                buf = ['\0'] * (str_len + 1)
                buf[:str_len] = str
                buf[str_len] = '\0'
                self.len_ = str_len
                self.external_str_ = buf
                self.chars_[self.MAX_EMBEDDED_LEN] = chr(self.STR_EXTERNALLY_STORED)
            else:
                str_len = len(str)
                self.chars_ = list(str) + ['\0'] * (self.MAX_EMBEDDED_LEN - str_len)
                self.chars_[self.MAX_EMBEDDED_LEN] = chr(str_len)

    def init_embedded(self, str_len1, str1, str_len2, str2):
        str_len = str_len1 + str_len2
        if str_len > self.MAX_EMBEDDED_LEN:
            raise Exception("Str::init_embedded(): combined length is too long to be embedded")
        self.chars_ = list(str1 + str2) + ['\0'] * (self.MAX_EMBEDDED_LEN - str_len)
        self.chars_[self.MAX_EMBEDDED_LEN] = chr(str_len)

    def init_external(self, str_len1, str1, str_len2, str2):
        str_len = str_len1 + str_len2
        if str_len <= self.MAX_EMBEDDED_LEN:
            raise Exception("Str::init_external(): combined length is too short to be external")
        buf = list(str1 + str2) + ['\0']
        self.len_ = str_len
        self.external_str_ = buf
        self.chars_[self.MAX_EMBEDDED_LEN] = chr(self.STR_EXTERNALLY_STORED)

    def deallocate_external_str(self):
        if not self.is_embedded():
            del self.external_str_

    def set(self, str):
        if not self.is_embedded():
            if str == self.external_str_:
                return
            old_external_str = self.external_str_
            self.init(str)
            del old_external_str
        else:
            if str == self.chars_:
                return
            self.init(str)

    def set_length(self, str_len):
        self.deallocate_external_str()
        self.init(str_len)

    def set_str(self, str, str_len):
        if not self.is_embedded():
            old_external_str = self.external_str_
            self.init(str, str_len)
            del old_external_str
        else:
            if str == self.chars_:
                return
            self.init(str, str_len)

    def __eq__(self, other):
        if isinstance(other, Str):
            return self.c_str() == other.c_str()
        elif isinstance(other, str):
            return self.c_str() == other
        return False

    def __add__(self, other):
        if isinstance(other, Str):
            str_len1 = self.length()
            str_len2 = other.length()
            if str_len1 + str_len2 <= self.MAX_EMBEDDED_LEN:
                return Str(str_len1, str_len2, self.c_str(), other.c_str())
            return Str(self.c_str(), other.c_str(), str_len1, str_len2)
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Str):
            return self.c_str() < other.c_str()
        return NotImplemented

    def __hash__(self):
        return hash(self.c_str())
