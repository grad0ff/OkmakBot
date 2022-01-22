import time
import pytz
from datetime import datetime


class Services():
    @staticmethod
    def time_checker(func):
        """проверяет время выполнения"""

        def wrapper(*args, **kwargs):
            t1 = time.time()
            func(*args, **kwargs)
            t2 = time.time()
            print(t2 - t1)

        return wrapper

    @staticmethod
    def get_datetime():
        tz_Moscow = pytz.timezone('Europe/Moscow')
        timestamp = repr(datetime.now(tz_Moscow).strftime("%H:%M %d.%m.%y"))
        return timestamp
