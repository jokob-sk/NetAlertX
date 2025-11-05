#!/usr/bin/env python

import os
import pathlib
import sys
from datetime import datetime
import datetime
import pytz
from pytz import timezone
from typing import Union
from zoneinfo import ZoneInfo
import email.utils

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

import conf
from const import *



#-------------------------------------------------------------------------------
# DateTime
#-------------------------------------------------------------------------------
def timeNowTZ():
    if conf.tz:
        return datetime.datetime.now(conf.tz).replace(microsecond=0)
    else:
        return datetime.datetime.now().replace(microsecond=0)

def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

def get_timezone_offset():    
    now = datetime.datetime.now(conf.tz)
    offset_hours = now.utcoffset().total_seconds() / 3600        
    offset_formatted =  "{:+03d}:{:02d}".format(int(offset_hours), int((offset_hours % 1) * 60))
    return offset_formatted

def timeNowDB(local=True):
    """
    Return the current time (local or UTC) as ISO 8601 for DB storage.
    Safe for SQLite, PostgreSQL, etc.

    Example local: '2025-11-04 18:09:11'
    Example UTC:   '2025-11-04 07:09:11'
    """
    if local:
        try:
            if isinstance(conf.tz, datetime.tzinfo):
                tz = conf.tz
            elif conf.tz:
                tz = ZoneInfo(conf.tz)
            else:
                tz = None
        except Exception:
            tz = None
        return datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')


#-------------------------------------------------------------------------------
#  Date and time methods
#-------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------
def format_date_iso(date1: str) -> str:
    """Return ISO 8601 string for a date or None if empty"""
    if date1 is None:
        return None
    dt = datetime.datetime.fromisoformat(date1) if isinstance(date1, str) else date1
    return dt.isoformat()

# -------------------------------------------------------------------------------------------
def format_event_date(date_str: str, event_type: str) -> str:
    """Format event date with fallback rules."""
    if date_str:
        return format_date(date_str)
    elif event_type == "<missing event>":
        return "<missing event>"
    else:
        return "<still connected>"

# -------------------------------------------------------------------------------------------
def ensure_datetime(dt: Union[str, datetime.datetime, None]) -> datetime.datetime:
    if dt is None:
        return timeNowTZ()
    if isinstance(dt, str):
        return datetime.datetime.fromisoformat(dt)
    return dt


def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        # Try ISO8601 first
        return datetime.datetime.fromisoformat(dt_str)
    except ValueError:
        # Try RFC1123 / HTTP format
        try:
            return datetime.datetime.strptime(dt_str, '%a, %d %b %Y %H:%M:%S GMT')
        except ValueError:
            return None

def format_date(date_str: str) -> str:
    try:
        dt = parse_datetime(date_str)
        if dt.tzinfo is None:
            # Set timezone if missing — change to timezone.utc if you prefer UTC
            now = datetime.datetime.now(conf.tz)
            dt = dt.replace(tzinfo=now.astimezone().tzinfo)
        return dt.astimezone().isoformat()
    except (ValueError, AttributeError, TypeError):
        return "invalid"

def format_date_diff(date1, date2, tz_name):
    """
    Return difference between two datetimes as 'Xd   HH:MM'.
    Uses app timezone if datetime is naive.
    date2 can be None (uses now).
    """
    # Get timezone from settings    
    tz = pytz.timezone(tz_name)

    def parse_dt(dt):
        if dt is None:
            return datetime.datetime.now(tz)
        if isinstance(dt, str):
            try:
                dt_parsed = email.utils.parsedate_to_datetime(dt)
            except (ValueError, TypeError):
             # fallback: parse ISO string
             dt_parsed = datetime.datetime.fromisoformat(dt)
            # convert naive GMT/UTC to app timezone
            if dt_parsed.tzinfo is None:
                dt_parsed = tz.localize(dt_parsed)
            else:
                dt_parsed = dt_parsed.astimezone(tz)
            return dt_parsed
        return dt if dt.tzinfo else tz.localize(dt)

    dt1 = parse_dt(date1)
    dt2 = parse_dt(date2)

    delta = dt2 - dt1
    total_minutes = int(delta.total_seconds() // 60)
    days, rem_minutes = divmod(total_minutes, 1440)  # 1440 mins in a day
    hours, minutes = divmod(rem_minutes, 60)

    return {
        "text": f"{days}d {hours:02}:{minutes:02}",
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "total_minutes": total_minutes
    }