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
    def init(self, str_len):
        if str_len <= self.MAX_EMBEDDED_LEN:
            self.chars_ = ['\0'] * (str_len + 1)
            self.chars_[self.MAX_EMBEDDED_LEN] = chr(str_len)
        else:
            self.len_ = str_len
            self.external_str_ = ['\0'] * (str_len + 1)
            self.chars_[self.MAX_EMBEDDED_LEN] = chr(self.STR_EXTERNALLY_STORED)

    def store_int_as_str(self, val):
        c = [''] * self.MAX_EMBEDDED_LEN
        size = 0
        if val >= 10000000000:
            if val >= 10000000000000:
                if val >= 1000000000000000:
                    size = 16
                elif val >= 100000000000000:
                    size = 15
                else:
                    size = 14
            else:
                if val >= 1000000000000:
                    size = 13
                elif val >= 100000000000:
                    size = 12
                else:
                    size = 11
        else:
            if val >= 10000:
                if val >= 10000000:
                    if val >= 1000000000:
                        size = 10
                    elif val >= 100000000:
                        size = 9
                    else:
                        size = 8
                else:
                    if val >= 1000000:
                        size = 7
                    elif val >= 100000:
                        size = 6
                    else:
                        size = 5
            else:
                if val >= 100:
                    if val >= 1000:
                        size = 4
                    else:
                        size = 3
                else:
                    if val >= 10:
                        size = 2
                    elif val == 0:
                        c[0] = '0'
                        c[1] = '\0'
                        self.chars_[self.MAX_EMBEDDED_LEN] = chr(1)
                        return ''.join(c)
                    else:
                        size = 1

        c = c[:size]
        while val >= 100:
            pos = val % 100
            val //= 100
            c[size-1] = self.digit_pairs[2*pos+1]
            c[size-2] = self.digit_pairs[2*pos]
            size -= 2
        while val > 0:
            c[size-1] = chr(48 + (val % 10))
            val //= 10
            size -= 1
        c.append('\0')
        if len(c) < self.MAX_EMBEDDED_LEN:
            self.chars_[self.MAX_EMBEDDED_LEN] = chr(len(c) - 1)
        return ''.join(c)
