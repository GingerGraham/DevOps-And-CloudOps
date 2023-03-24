#!/usr/bin/env python3

"""File system utilities
"""


# Import global modules
import os
from pathlib import PureWindowsPath, PurePosixPath


def create_log_file(log_path):
    """Create Log File

    This function creates the log file if it does not exist and handles Windows vs Linux pathing.

    Args:
        log_path (str): Path to log file

    Returns:
        log_path (str): Path to log file

    Output:
        Creates target directory and log file if they do not exist

    """
    try:

        # Split the path into directory and file name
        # Handle if ~ is passed as the log file location
        log_path = os.path.expanduser(log_path)

        # If OS is Windows, replace \ with / to avoid errors
        if os.name == 'nt':\
            log_path = PureWindowsPath(log_path)

        if os.name == 'posix':
            log_path = PurePosixPath(log_path)

        # Split the path into directory and file name
        # filename = os.path.basename(path) # Optionally get the file name
        directory = os.path.dirname(log_path)

        # Test if the directory exists
        if not os.path.exists(directory):
            print("Creating directory: {0}".format(directory))
            os.makedirs(directory)

        # Test if the file exists
        if not os.path.exists(log_path):
            print("Creating file: {0}".format(log_path))
            open(log_path, 'a').close()

        # Return the path
        return log_path


    except Exception as e:
        print("An error occurred in create_log_file: {}".format(e))
        return 1