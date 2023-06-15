"""
Different helper classes for the scripts
"""
from datetime import datetime, timedelta
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