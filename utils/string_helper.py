class StringStr:
    def __init__(self):
        self._str = []

    def __lshift__(self, other):
        self._str.append(str(other))
        return self

    def __str__(self):
        return ''.join(self._str)

    def str(self):
        return ''.join(self._str)

    def c_str(self):
        return ''.join(self._str)


# Example usage
if __name__ == "__main__":
    foo, bar = 10, 20
    try:
        raise RuntimeError(StringStr() << "Error because " << foo << " doesn't equal " << bar)
    except RuntimeError as e:
        print(e)
