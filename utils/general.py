import datetime

import pandas as pd



# Check peak hour
def time_in_period(x, y, start, end):
    """Return true if x is in the range [start, end]"""
    if not isinstance(start, datetime.time):
        start = float_to_time(start)
        end = float_to_time(end)
    if end == datetime.time(0, 0, 0):
        end = datetime.time(23, 59, 59)
    if y < x:
        x1 = x
        y1 = datetime.time(23, 59, 59)
        x2 = datetime.time(0, 0, 0)
        y2 = y
    else:
        x1 = x
        x2 = x
        y1 = y
        y2 = y
    return (start <= x1 < end or start < y1 <= end) or (x1 < start and y1 > end) or \
           (start <= x2 < end or start < y2 <= end) or (x2 < start and y2 > end)


def float_to_time(x):
    time = int(x) * 60
    return datetime.time(divmod(time, 60)[0], divmod(time, 60)[1], 0)

