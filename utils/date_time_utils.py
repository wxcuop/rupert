from datetime import datetime, timedelta

class DateAndTime:
    def __init__(self, year=None, month=None, day=None, hour=0, minute=0, second=0, millis=0):
        if year is None or month is None or day is None:
            self.dt = datetime.utcnow()
        else:
            self.dt = datetime(year, month, day, hour, minute, second, millis * 1000)

    @classmethod
    def from_hhmm(cls, hhmm):
        try:
            hour, minute = map(int, hhmm.split(':'))
            now = datetime.utcnow()
            return cls(now.year, now.month, now.day, hour, minute)
        except ValueError:
            raise ValueError(f"Unable to parse date {hhmm}")

    def get_year(self):
        return self.dt.year

    def get_month(self):
        return self.dt.month

    def get_day(self):
        return self.dt.day

    def get_hour(self):
        return self.dt.hour

    def get_minute(self):
        return self.dt.minute

    def get_second(self):
        return self.dt.second

    def get_millisecond(self):
        return self.dt.microsecond // 1000

    def set_year(self, year):
        self.dt = self.dt.replace(year=year)

    def set_month(self, month):
        self.dt = self.dt.replace(month=month)

    def set_day(self, day):
        self.dt = self.dt.replace(day=day)

    def set_hour(self, hour):
        self.dt = self.dt.replace(hour=hour)

    def set_minute(self, minute):
        self.dt = self.dt.replace(minute=minute)

    def set_second(self, second):
        self.dt = self.dt.replace(second=second)

    def set_millisecond(self, millis):
        self.dt = self.dt.replace(microsecond=millis * 1000)

    def to_timestamp(self):
        return self.dt.timestamp()

    def to_utc(self):
        return self.dt.utcnow()

    def __str__(self):
        return self.dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
