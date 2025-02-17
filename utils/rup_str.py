class Str:
    MAX_EMBEDDED_LEN = 15
    STR_EXTERNALLY_STORED = 0xFF

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
