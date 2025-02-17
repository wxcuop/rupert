import os
import tempfile
from datetime import timezone, timedelta

class TimezoneDB:
    _instance = None
    tz_data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimezoneDB, cls).__new__(cls)
            cls._instance.load_timezone_data()
        return cls._instance

    def load_timezone_data(self):
        # The content of date_time_zonespec_csv should be provided as a string
        date_time_zonespec_csv = """
        Europe/London,0,0
        America/New_York,-5,0
        """
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(date_time_zonespec_csv.encode())
            temp_file.close()
            self._load_from_file(temp_file.name)
        finally:
            if temp_file:
                os.remove(temp_file.name)

    def _load_from_file(self, file_path):
        with open(file_path, 'r') as file:
            for line in file:
                region, offset_hours, offset_minutes = line.strip().split(',')
                self.tz_data[region] = timezone(timedelta(hours=int(offset_hours), minutes=int(offset_minutes)))

    def get(self, tz):
        if tz in self.tz_data:
            return self.tz_data[tz]
        else:
            raise RuntimeError("Unable to load timezone")

# Example usage
if __name__ == "__main__":
    tz_db = TimezoneDB()
    timezone = tz_db.get("Europe/London")
    print(timezone)
    now = datetime.now(timezone)
    print(now)
