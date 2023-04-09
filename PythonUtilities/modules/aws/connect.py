#!/usr/bin/env python3

"""AWS utilities
"""


# Import global modules
import logging
import os
from os import environ
import sys

# Import local modules
import modules.output as output

# Import third party modules - see requirements.txt
import boto3
from botocore.exceptions import ClientError

def aws_connect(profile, region):
    """Connect to AWS

    This function connects to AWS using the AWS CLI credentials or AWS Session Token and creates a boto3 session.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()

    Returns:
        aws_session (boto3.session.Session): AWS Session
        1 (int): If an error occurs

    """

    try:
        logging.debug(f"Function: _aws_connect() started with args: profile = {profile}, region = {region}")

        logging.info("Connecting to AWS")

        # Test if AWS CLI credentials are configured and that the passed profile exists by using _check_aws_profile() and looking for a 0 return code, if a 0 return code is found use the profile and region passed to the script to create a boto3 session
        if _check_aws_profile(profile) == 0:
            aws_session = boto3.Session(profile_name=profile,region_name=region)
            # Print AWS Session Details using _print_aws_session_details() and then return to main()
            _print_aws_session_details(aws_session)
            logging.debug(f"Account ID: {get_aws_account_id(aws_session)}")
            logging.debug("Function: _aws_connect() completed")
            return aws_session
        # Test if AWS Session Token is set in the environment and if so use them to create a boto3 session
        if _check_aws_vars() == 0:
            aws_session = boto3.Session()
            # Print AWS Session Details using _print_aws_session_details() and then return to main()
            _print_aws_session_details(aws_session)
            logging.debug(f"Account ID: {get_aws_account_id(aws_session)}")
            logging.debug("Function: _aws_connect() completed")
            return aws_session

        # If neither the passed profile or AWS Session Token are set in the environment then exit with an error
        logging.error("AWS CLI credentials are not configured or the profile passed does not exist")
        logging.warning("Please configure AWS CLI credentials or set AWS Session Tokens in the environment variables")
        return 1

    except ClientError as e:
        logging.error("Client Error in _aws_connect: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _aws_connect: {0}".format(sys.exc_info()[0]))
        return 1


def get_aws_account_id(aws_session):
    """Lookup AWS Account ID

    This function looks up the AWS Account ID using the AWS Session.

    Args:
        aws_session (boto3.session.Session): AWS Session

    Returns:
        str: AWS Account ID
    """
    try:
        logging.debug(f"Function: get_aws_Account_id() started with args: aws_session = {aws_session}")

        logging.debug("Looking up AWS Account ID")

        aws_account_id = aws_session.client('sts').get_caller_identity().get('Account')

        logging.debug(f"Returned AWS Account ID: {aws_account_id}")
        logging.debug("Function: _get_aws_Account_id() completed")

        return aws_account_id

    except ClientError as e:
        logging.error(f"Error in _get_aws_Account_id: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in _get_aws_Account_id: {sys.exc_info()[0]}")
        return 1


def session_connect(**kwargs):
    """Session Connect

    This function establishes a specified client connection to AWS using the passed AWS Session.

    Args:
        aws_session (boto3.session.Session): AWS Session
        client_type (str): AWS Client Type e.g. ec2, s3, etc.
        region (str): AWS Region

    Returns:
        client (boto3.client): AWS Client

    Example:
        client = session_connect(aws_session=aws_session, client_type='ec2', region='eu-west-1')

    """
    try:
        logging.debug(f"Function: session_connect() started with args: {kwargs}")

        logging.debug("Connecting to AWS")

        if 'aws_session' in kwargs:
            aws_session = kwargs['aws_session']
        else:
            logging.error("No AWS Session passed to session_connect()")
            return 1

        if 'client_type' in kwargs:
            client_type = kwargs['client_type']
        else:
            logging.error("No client type passed to session_connect()")
            return 1

        if 'region' in kwargs:
            region = kwargs['region']
        else:
            region = aws_session.region_name

        client = aws_session.client(client_type, region_name=region)

        logging.debug((f"Returning client session: {client}"))

        logging.debug(f"Function: session_connect() completed")

        return client

    except ClientError as e:
        logging.error(f"Client Error in session_connect(): {e}")
        return 1
    except:
        logging.error(f"Unexpected error in session_connect(): {sys.exc_info()[0]}")
        return 1


def _check_aws_profile(profile):
    """Check if the passed AWS Profile exists

    This function checks if the passed AWS Profile exists in the AWS CLI credentials file.

    Args:
        profile (str): AWS Profile

    Returns:
        int: 0 if the AWS Profile exists, 1 if the AWS Profile does not exist

    """
    # Check if AWS CLI credentials are configured and that the passed profile exists
    try:
        logging.debug("Function: _check_aws_profile() started with args: profile = {}".format(profile))

        logging.info("Checking AWS CLI credentials")

        # Test if AWS CLI credentials exists
        logging.debug("Checking if AWS CLI credentials exist")
        if not os.path.isfile(os.path.expanduser('~/.aws/credentials')):
            logging.warning("AWS CLI credentials are not configured")
            return 1
        logging.debug("AWS CLI credentials exist")

        # Get AWS Profiles from AWS CLI credentials file
        logging.debug("Getting AWS Profiles from AWS CLI credentials file")
        aws_profiles = []
        with open(os.path.expanduser('~/.aws/credentials'), 'r') as f:
            for line in f:
                if line.startswith('['):
                    aws_profiles.append(line.strip('[]\n'))
        logging.debug("AWS Profiles: {0}".format(aws_profiles))

        if profile in aws_profiles:
            logging.info("AWS CLI credentials are configured and profile {0} exists".format(profile))
            logging.debug("Function: _check_aws_profile() completed")
            return 0
        else:
            logging.error("AWS CLI credentials are not configured or profile {0} does not exist".format(profile))
            logging.debug("Function: _check_aws_profile() completed")
            return 1

    except ClientError as e:
        logging.error("Error in _check_aws_profile: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _check_aws_profile: {0}".format(sys.exc_info()[0]))
        return 1


def _print_aws_session_details(aws_session):
    """Print AWS Session Details

    This function prints the AWS Session details to stdout.

    Args:
        aws_session (boto3.session.Session): AWS Session

    Returns:
        None
    """
    try:
        logging.debug("Function: _print_aws_session_details() started with args: aws_session = {}".format(aws_session))

        output.log_message_section("AWS Session Details:", top=False, bottom=False)

        logging.info("Profile: {0}".format(aws_session.profile_name))
        logging.info("Region: {0}".format(aws_session.region_name))
        logging.info("User: {0}".format(aws_session.client('sts').get_caller_identity().get('Arn')))
        logging.debug("AWS Session: {0}".format(aws_session))

        output.log_message_section("Connected to AWS", top=False, bottom=False)

        logging.debug("Function: _print_aws_session_details() completed")

    except ClientError as e:
        logging.error("Error in _print_aws_session_details: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _print_aws_session_details: {0}".format(sys.exc_info()[0]))
        return 1


def _check_aws_vars():
    """Check if AWS variables are set

    This function checks if the AWS variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and optionally AWS_SESSION_TOKEN are set in the environment.

    Returns:
        0 if all required variables are set
        1 if AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY are not set
    """
    # Check if AWS variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and optionally AWS_SESSION_TOKEN are set
    try:
        # logging.debug("Function: _check_aws_vars() started")

        # Check if AWS_ACCESS_KEY_ID is set
        if environ.get('AWS_ACCESS_KEY_ID') is None:
            logging.error("AWS_ACCESS_KEY_ID is not set")
            logging.debug("Function: _check_aws_vars() completed")
            return 1
        if environ.get('AWS_SECRET_ACCESS_KEY') is None:
            logging.error("AWS_SECRET_ACCESS_KEY is not set")
            logging.debug("Function: _check_aws_vars() completed")
            return 1
        if environ.get('AWS_SESSION_TOKEN') is None:
            logging.warning("AWS_SESSION_TOKEN is not set, ensure that the configured AWS User does not require MFA")
            logging.debug("Function: _check_aws_vars() completed")
            return 0
        # If all variables are set then return 0
        logging.info("AWS variables are set")
        # logging.debug("Function: _check_aws_vars() completed")
        return 0

    except ClientError as e:
        logging.error("Error in _check_aws_vars: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _check_aws_vars: {0}".format(sys.exc_info()[0]))
        return 1


