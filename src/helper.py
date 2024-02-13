"""
Different helper classes for the scripts
"""
from datetime import datetime, timedelta
import os
# pylint: disable=import-error
import pytz

def is_dst(zonename):
    """
    Find out if a timezone currently in daylight savings time
    """
    zonename = str(zonename)
    timezone = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.utcnow())
    return now.astimezone(timezone).dst() != timedelta(0)

def log_rotate(logging_file_path: str):
    if os.path.isfile("var/bot.log"):
        i = 1
        while True:
            if os.path.isfile(f"{logging_file_path}.{i}"):
                i += 1
            else:
                os.rename(logging_file_path, f"{logging_file_path}.{i}")
                break