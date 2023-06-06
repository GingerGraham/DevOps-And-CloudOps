#!/usr/bin/env python3

"""Output utilities

Provides functions to print messages to the console, and depending on configuration to a log file.

Functions:

log_message_section: Print a message with a divider using the logging module
print_message_section: Print a message with a divider using the print function

"""


import logging


def log_message_section(message, top=True, bottom=False, divider="="):
    """Print a message with a divider

    This function prints a message with a divider above and below the message using the logging module.

    Args:
        message (str): Message to be printed
        top (bool): Print divider above message
        bottom (bool): Print divider below message
        divider (str): Divider to be used

    Returns:
        None

    Example:
        log_message_section("This is a message", top=True, bottom=True, divider="=")

    Output:
        ===================
        This is a message
        ===================

    Example:
        log_message_section("This is a message", top=True, bottom=False, divider="*")

    Output:
        ******************
        This is a message

    """
    if top:
        logging.info(divider * len(message))
    logging.info(message)
    if bottom:
        logging.info(divider * len(message))


def print_message_section(message, top=True, bottom=False, divider="="):
    """Print a message with a divider

    This function prints a message with a divider above and below the message using the print function.

    Args:
        message (str): Message to be printed
        top (bool): Print divider above message
        bottom (bool): Print divider below message
        divider (str): Divider to be used

    Returns:
        None

    Example:
        print_message_section("This is a message", top=True, bottom=True, divider="=")

    Output:
        ===================
        This is a message
        ===================

    Example:
        print_message_section("This is a message", top=True, bottom=False, divider="*")

    Output:
        ******************
        This is a message

    # """

    if top:
        print(divider * len(message))
    print(message)
    if bottom:
        print(divider * len(message))