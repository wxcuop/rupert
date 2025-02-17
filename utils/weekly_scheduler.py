import os
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, List, Set, Optional

callback_fn_t = Callable[[Optional[datetime]], None]
timer_id_t = int

class WeeklyTimer:
    def cancel(self):
        raise NotImplementedError()

    def register_callback(self, timer_id: timer_id_t, fn: callback_fn_t, scheduler: 'WeeklyScheduler'):
        raise NotImplementedError()

    def expires_at(self, next_event_time: datetime):
        raise NotImplementedError()

    def get_expiry_time(self) -> datetime:
        raise NotImplementedError()

class DefaultTimerImpl(WeeklyTimer):
    io_service = None

    def __init__(self, next_event_time: datetime):
        self.timer = threading.Timer((next_event_time - datetime.now()).total_seconds(), self._timer_callback)
        self.callback = None
        self.scheduler = None
        self.timer_id = None

    def _timer_callback(self):
        if self.callback:
            self.callback()
        if self.scheduler:
            self.scheduler.recurring_timer_event(None, self.timer_id, self.callback)

    def cancel(self):
        self.timer.cancel()

    def register_callback(self, timer_id: timer_id_t, fn: callback_fn_t, scheduler: 'WeeklyScheduler'):
        self.callback = fn
        self.scheduler = scheduler
        self.timer_id = timer_id

    def expires_at(self, next_event_time: datetime):
        self.timer = threading.Timer((next_event_time - datetime.now()).total_seconds(), self._timer_callback)

    def get_expiry_time(self) -> datetime:
        return self.timer.interval + datetime.now()

class WeeklyScheduler:
    short_weekday_names = ["Su", "M", "T", "W", "Th", "F", "Sa"]
    timer_thread = None

    def __init__(self):
        self.schedules: List[Set[datetime]] = []
        self.timers: List[WeeklyTimer] = []
        self.lock = threading.Lock()
        self.thread_instance = None

    def generate_schedule_date(self, short_day: str, first_day_of_this_week: datetime, hours: str, mins: str, secs: str) -> datetime:
        days = {'Su': 6, 'M': 0, 'T': 1, 'W': 2, 'Th': 3, 'F': 4, 'Sa': 5}
        day_delta = days[short_day] - first_day_of_this_week.weekday()
        if day_delta < 0:
            day_delta += 7
        schedule_date = first_day_of_this_week + timedelta(days=day_delta)
        return schedule_date.replace(hour=int(hours), minute=int(mins), second=int(secs))

    def create_timer(self, next_event_time: datetime) -> WeeklyTimer:
        timer = DefaultTimerImpl(next_event_time)
        self.timers.append(timer)
        return timer

    def recurring_timer_event(self, e, timer_id: timer_id_t, event_callback: callback_fn_t):
        if e:
            print(f"Error occurred: {e}")
        else:
            events = self.schedules[timer_id]
            next_event_time = min(events)
            events.remove(next_event_time)
            next_event_time += timedelta(weeks=1)
            events.add(next_event_time)
            timer = self.create_timer(next_event_time)
            timer.register_callback(timer_id, event_callback, self)
            timer.expires_at(next_event_time)

    def register_event(self, schedule_spec: str, time_zone: str, callback: callback_fn_t) -> timer_id_t:
        schedule_split = schedule_spec.split(';')
        old_tz = os.getenv('TZ')
        if time_zone:
            os.environ['TZ'] = time_zone
            time.tzset()

        today = datetime.now()
        utc_offset = datetime.utcnow() - datetime.now()
        first_day_of_this_week = today - timedelta(days=today.weekday())
        
        events = set()
        time_regex = r"([0-2]\d):(\d\d)(:[0-5]\d)?"

        for schedule_item in schedule_split:
            time_match = re.match(f"^{time_regex}$", schedule_item)
            if time_match:
                hour, minute, second = time_match.groups()
                second = second[1:] if second else "00"
                first_day = self.short_weekday_names[0]
                end_day = self.short_weekday_names[-1]
            else:
                day_time_match = re.match(f"^({'|'.join(self.short_weekday_names)})-({'|'.join(self.short_weekday_names)}),{time_regex}$", schedule_item)
                if not day_time_match:
                    raise ValueError(f"Failed to parse {schedule_item}")
                first_day, end_day, hour, minute, second = day_time_match.groups()
                second = second[1:] if second else "00"

            range_start = self.generate_schedule_date(first_day, first_day_of_this_week, hour, minute, second)
            range_end = self.generate_schedule_date(end_day, first_day_of_this_week, hour, minute, second)

            while range_start <= range_end:
                events.add(range_start + utc_offset)
                range_start += timedelta(days=1)

        if time_zone:
            if old_tz is not None:
                os.environ['TZ'] = old_tz
            else:
                del os.environ['TZ']
            time.tzset()

        self.schedules.append(events)
        timer_id = len(self.schedules) - 1
        next_event_time = self.get_date_of_next_event(timer_id)
        if not next_event_time:
            print("No more events scheduled")
        else:
            timer = self.create_timer(next_event_time)
            self.timers.append(timer)
            timer.register_callback(timer_id, callback, self)
        return timer_id

    def get_date_of_next_event(self, timer_id: timer_id_t) -> Optional[datetime]:
        now = datetime.utcnow() + timedelta(minutes=1)
        events = self.schedules[timer_id]
        next_event = min(event for event in events if event >= now)
        return next_event

    def start(self):
        if not self.timer_thread:
            self.timer_thread = threading.Thread(target=self._run)
            self.timer_thread.start()

    def _run(self):
        while True:
            time.sleep(1)

    def clear(self):
        for timer in self.timers:
            timer.cancel()
        self.schedules.clear()
        self.timers.clear()

    def get_events(self, timer_id: timer_id_t) -> Set[datetime]:
        return self.schedules[timer_id]

    def get_timer_id_size(self) -> int:
        return len(self.schedules)

# Example usage
if __name__ == "__main__":
    scheduler = WeeklyScheduler()

    def my_callback(event_time: Optional[datetime]):
        print(f"Event triggered at {event_time}")

    scheduler.register_event("M,10:00;W,14:00", "UTC", my_callback)
    scheduler.start()
