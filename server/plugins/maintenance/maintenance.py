#!/usr/bin/env python

import os
import sys

# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
from messaging.in_app import remove_old  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import timeNowUTC  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'MAINT'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


def main():

    mylog('verbose', [f'[{pluginName}] In script'])

    MAINT_LOG_LENGTH = int(get_setting_value('MAINT_LOG_LENGTH'))
    MAINT_NOTI_LENGTH = int(get_setting_value('MAINT_NOTI_LENGTH'))

    logFiles = ["app.log", "nginx-error.log"]

    # Check if set
    if MAINT_LOG_LENGTH != 0:

        MAX_TAIL_SIZE = MAINT_LOG_LENGTH * 80  # Bytes = lines * approx 80 chars per log line

        for fileEntry in logFiles:

            logFile = os.path.join(logPath, fileEntry)

            if not os.path.isfile(logFile):
                mylog('verbose', [f'[{pluginName}] File not found: {fileEntry}'])
                continue

            size_before = os.path.getsize(logFile)

            mylog('verbose', [f'[{pluginName}] {fileEntry} size BEFORE: {size_before}'])

            try:

                if size_before <= MAX_TAIL_SIZE:
                    mylog('verbose', [f'[{pluginName}] {fileEntry} already within limit, skipping'])
                else:
                    mylog('verbose', [f'[{pluginName}] {fileEntry} exceeds limit, trimming to last {MAINT_LOG_LENGTH} lines'])

                    lines_to_keep = tail_file(logFile, MAINT_LOG_LENGTH)

                    with open(logFile, 'r+b') as f:
                        f.seek(0)
                        f.truncate()
                        f.writelines(lines_to_keep)

                size_after = os.path.getsize(logFile)

                mylog('verbose', [f'[{pluginName}] {fileEntry} size AFTER: {size_after}'])

            except Exception as e:
                mylog('none', [f'[{pluginName}] Failed to clean {fileEntry}: {e}'])

    # Check if set
    if MAINT_NOTI_LENGTH != 0:
        mylog('verbose', [f'[{pluginName}] Cleaning in-app notification history'])
        remove_old(MAINT_NOTI_LENGTH)

    # Delete processed sync artefact files older than 24 hours.
    # These are created by the SYNC plugin (Mode 3) when it renames received
    # device JSON files to processed_*.log after processing. They have no value
    # once processed and are not cleaned up anywhere else.
    _PROCESSED_MAX_AGE_SECS = 24 * 3600
    now = timeNowUTC(as_string=False).timestamp()
    deleted = 0
    for fname in os.listdir(LOG_PATH):
        if fname.startswith('processed_') and fname.endswith('.log'):
            fpath = os.path.join(LOG_PATH, fname)
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > _PROCESSED_MAX_AGE_SECS:
                os.remove(fpath)
                deleted += 1
    mylog('verbose', [f'[{pluginName}] Deleted {deleted} processed sync artefact file(s) from {LOG_PATH}'])

    return 0


def tail_file(filepath, num_lines):
    """
    Return the last num_lines lines from a file without reading the entire file.
    """
    if num_lines <= 0:
        return []

    block_size = 8192

    with open(filepath, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        blocks = []
        lines_found = 0
        position = file_size

        while position > 0 and lines_found <= num_lines:
            read_size = min(block_size, position)
            position -= read_size

            f.seek(position)
            block = f.read(read_size)

            blocks.append(block)
            lines_found += block.count(b'\n')

        data = b''.join(reversed(blocks))
        return data.splitlines(keepends=True)[-num_lines:]


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
