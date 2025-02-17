from datetime import datetime, timedelta

class TimestampData:
    def __init__(self, wsec=0, nsec=0):
        self.wsec = wsec
        self.nsec = nsec

    def normalize(self):
        if self.nsec > 1e9:
            self.wsec += 1
            self.nsec -= 1e9
        elif self.nsec < -1e9:
            self.wsec -= 1
            self.nsec += 1e9
        if self.wsec > 0 and self.nsec < 0:
            self.wsec -= 1
            self.nsec += 1e9
        elif self.wsec < 0 and self.nsec > 0:
            self.wsec += 1
            self.nsec -= 1e9

class TimeInterval:
    def __init__(self, wsec=0, nsec=0):
        self.interval = TimestampData(wsec, nsec)

    def __sub__(self, other):
        result = TimeInterval(self.interval.wsec - other.interval.wsec, self.interval.nsec - other.interval.nsec)
        result.interval.normalize()
        return result

    def __add__(self, other):
        result = TimeInterval(self.interval.wsec + other.interval.wsec, self.interval.nsec + other.interval.nsec)
        result.interval.normalize()
        return result

    def __eq__(self, other):
        return self.interval.wsec == other.interval.wsec and self.interval.nsec == other.interval.nsec

    def __iadd__(self, other):
        self.interval.wsec += other.interval.wsec
        self.interval.nsec += other.interval.nsec
        self.interval.normalize()
        return self

    def __isub__(self, other):
        self.interval.wsec -= other.interval.wsec
        self.interval.nsec -= other.interval.nsec
        self.interval.normalize()
        return self

    def to_timestamp_data(self):
        return self.interval

    def to_double(self):
        return self.interval.wsec + self.interval.nsec / 1e9

    def get_milliseconds(self):
        return self.interval.wsec * 1000 + self.interval.nsec / 1e6

class Timestamp:
    base_ = datetime(1970, 1, 1)

    def __init__(self, *args):
        if len(args) == 1 and args[0] == 'NOW':
            self.set_now()
        elif len(args) == 7:
            self.timestamp_data = TimestampData(int(time.mktime(datetime(*args).timetuple())), args[6])
        else:
            self.timestamp_data = TimestampData(args[0], args[1]) if len(args) == 2 else TimestampData()

    def set_now(self):
        ts = datetime.now()
        self.timestamp_data = TimestampData(int(ts.timestamp()), ts.microsecond * 1000)
        return self

    def __eq__(self, other):
        return self.timestamp_data.wsec == other.timestamp_data.wsec and self.timestamp_data.nsec == other.timestamp_data.nsec

    def __iadd__(self, other):
        if isinstance(other, TimeInterval):
            self.timestamp_data.wsec += other.interval.wsec
            self.timestamp_data.nsec += other.interval.nsec
        else:
            inc = int(other)
            self.timestamp_data.wsec += inc
            self.timestamp_data.nsec += int((other - inc) * 1e9)
        self.timestamp_data.normalize()
        return self

    def __isub__(self, other):
        if isinstance(other, TimeInterval):
            self.timestamp_data.wsec -= other.interval.wsec
            self.timestamp_data.nsec -= other.interval.nsec
        else:
            dec = int(other)
            self.timestamp_data.wsec -= dec
            self.timestamp_data.nsec -= int((other - dec) * 1e9)
        self.timestamp_data.normalize()
        return self

    def to_timestamp_data(self):
        return self.timestamp_data

    def to_double(self):
        return self.timestamp_data.wsec + self.timestamp_data.nsec / 1e9

    def to_uint64(self):
        return (self.timestamp_data.wsec << 32) | self.timestamp_data.nsec

    def get_local_time_str(self):
        dt = datetime.fromtimestamp(self.timestamp_data.wsec)
        return dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{self.timestamp_data.nsec // 1e6:.0f}'

    def get_milliseconds(self):
        return self.timestamp_data.wsec * 1000 + self.timestamp_data.nsec / 1e6

    def __str__(self):
        return self.get_local_time_str()

# Example usage
if __name__ == "__main__":
    ts = Timestamp('NOW')
    print(ts)
    interval = TimeInterval(1, 500000000)
    ts += interval
    print(ts)
    ts -= interval
    print(ts)
