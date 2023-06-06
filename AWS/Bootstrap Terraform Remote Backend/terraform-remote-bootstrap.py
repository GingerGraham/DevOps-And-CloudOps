#!/usr/bin/env python3


"""Bootstrap Terraform Remote Backend

This script creates an S3 bucket and, optionally, a DynamoDB table which can be used as a remote backend for Terraform.

The script is written as a general purpose script which can be used to create an S3 bucket and DynamoDB table for any purpose. However, the script is designed to be used as a Terraform remote backend and so many of the options and arguments are specific to this use case.

The script is designed to be run from the command line and can be run with the following command:

    python3 terraform-remote-bootstrap.py

Alternatively, the script can be included as a module in another Python script and the create_s3_backend() can be called directly.

Args:
    Options:
    --------
    help: Displays help and usage information
    list_only (bool): List entities that would be created without creating them.  Also available with the --dry-run flag

    AWS Connection Details
    ----------------------
    aws-profile (str): AWS Profile to use.  Default is 'default'
    region (str): AWS Region to use.  Default is 'us-east-1'

    S3 Bucket Details
    -----------------
    bucket-name (str): S3 Bucket Name.  Default is 'terraform-remote-backend'
    bucket-region (str): S3 Bucket Region.  Default is to use the AWS Region specified
    bucket-versioning (bool): S3 Bucket Versioning.  Default is 'True'
    bucket-encryption (bool): S3 Bucket Encryption.  Default is 'True'
    bucket-kms-key-id (str): S3 Bucket KMS Key ID.
    bucket-public-access-block (bool): S3 Bucket Public Access Block.  Default is 'True'

    DynamoDB Table Details
    ----------------------
    dynamodb-table-enabled (bool): Enable DynamoDB Table.  Default is 'True'
    dynamodb-table-name (str): DynamoDB Table Name.  Default is 'terraform-remote-state'
    dynamodb-table-region (str): DynamoDB Table Region.  Default is to use the AWS Region specified
    dynamodb-table-read-capacity (int): DynamoDB Table Read Capacity.  Default is '5'
    dynamodb-table-write-capacity (int): DynamoDB Table Write Capacity.  Default is '5'

    Logging Details
    ---------------
    log-file: Log file to use.  Default is '/dev/null'
    log-level: Log level to use.  Default is 'INFO'

Returns:
    s3_bucket_name (str): S3 Bucket Name
    s3_bucket_region (str): S3 Bucket Region
    s3_kms_key_id (str): KMS Key ID
    dynamodb_table_name (str): DynamoDB Table Name

Examples:
    Generate help and usage information:

    python3 terraform-remote-bootstrap.py --help

    Create S3 bucket and DynamoDB table for Terraform remote backend using AWS access tokens from environment variables (no aws-profile and/or region specified):

    python3 terraform-remote-bootstrap.py --bucket-name "terraform-remote-backend" --bucket-region "us-east-1" --bucket-versioning "True" --bucket-encryption "True" --bucket-kms-key-id "alias/aws/s3" --bucket-public-access-block "True" --dynamodb-table-enabled "True" --dynamodb-table-name "terraform-remote-state" --dynamodb-table-region "us-east-1" --dynamodb-table-read-capacity "5" --dynamodb-table-write-capacity "5" --log-file "/var/log/terraform-remote-bootstrap.log" --log-level "INFO"

    Dry run of a create S3 bucket and DynamoDB table for Terraform remote backend using AWS access tokens from environment variables (no aws-profile and/or region specified) and list entities that would be created without creating them:

    python3 terraform-remote-bootstrap.py --bucket-name "terraform-remote-backend" --bucket-region "us-east-1" --bucket-versioning "True" --bucket-encryption "True" --bucket-kms-key-id "alias/aws/s3" --bucket-public-access-block "True" --dynamodb-table-enabled "True" --dynamodb-table-name "terraform-remote-state" --dynamodb-table-region "us-east-1" --dynamodb-table-read-capacity "5" --dynamodb-table-write-capacity "5" --log-file "/var/log/terraform-remote-bootstrap.log" --log-level "INFO" --list-only

    Running the script as a module:

    from terraform_remote_bootstrap import create_s3_backend:

    s3_bucket_name, s3_bucket_region, s3_kms_key_id, dynamodb_table_name = create_s3_backend(bucket_name="terraform-remote-backend", bucket_region="us-east-1", bucket_versioning=True, bucket_encryption=True, bucket_kms_key_id="alias/aws/s3", bucket_public_access_block=True, dynamodb_table_enabled=True, dynamodb_table_name="terraform-remote-state", dynamodb_table_region="us-east-1", dynamodb_table_read_capacity=5, dynamodb_table_write_capacity=5, log_file="/var/log/terraform-remote-bootstrap.log", log_level="INFO")

    Or:

    import sys
    import terraform_remote_bootstrap
    sys.argv = ['terraform-remote-bootstrap.py', '--bucket-name', 'terraform-remote-backend', '--bucket-region', 'us-east-1', '--bucket-versioning', 'True', '--bucket-encryption', 'True', '--bucket-kms-key-id', 'alias/aws/s3', '--bucket-public-access-block', 'True', '--dynamodb-table-enabled', 'True', '--dynamodb-table-name', 'terraform-remote-state', '--dynamodb-table-region', 'us-east-1', '--dynamodb-table-read-capacity', '5', '--dynamodb-table-write-capacity', '5', '--log-file', '/var/log/terraform-remote-bootstrap.log', '--log-level', 'INFO']
    terraform_remote_bootstrap.create_s3_backend()
"""


import sys
import os
import argparse
import logging
import subprocess
import boto3
from os import environ
from botocore.exceptions import ClientError,ParamValidationError
from datetime import datetime,timezone

# Global Variables
version = "1.0.1"
log_level=logging.INFO
log_format='%(asctime)s [%(levelname)s] %(message)s'
logging_file="/dev/null"
date = datetime.now().strftime('%Y-%m-%d')
timestamp = datetime.now(timezone.utc).strftime('%H:%M')
s3_bucket_name = None # S3 Bucket Name
s3_bucket_region = None # S3 Bucket Region
s3_kms_key_id = None # KMS Key ID
s3_kms_key_alias = None # KMS Key Alias
dynamodb_table = None # DynamoDB Table Name


def _main(passed_args=None):
    try:
        args = _parse_args(passed_args) # Parse arguments
        _configure_logging() # Configure logging
        _print_message_section("Terraform Remote Backend Bootstrap v{}".format(version), bottom=True) # Print script header
        _print_args(args) # Print arguments
        aws_session = _aws_connect(args.aws_profile, args.region) # Connect to AWS
        aws_account_id = _lookup_aws_account_id(aws_session)
        _create_s3_bucket(args, aws_account_id, aws_session) # Create S3 Bucket
        if args.dynamodb_table_enabled:
            _create_dynamodb_table(args, aws_account_id, aws_session) # Create DynamoDB Table
        _print_s3_and_dynamodb_backend_details() # Print S3 and DynamoDB backend details
        if args.list_only:
            _print_message_section("List only specified; NO CHANGES MADE!")
        _print_message_section("Terraform Remote Backend Bootstrap Completed!", top=True, bottom=False) # Print script footer

    except KeyboardInterrupt:
        logging.warning("Keyboard interrupt; exiting script")
        sys.exit(0)
    except Exception as e:
        logging.error("An error occurred in main: {}".format(e))
        sys.exit(1)


def _print_message_section(message, top=True, bottom=False, divider="="):
    """Print a message with a divider

    This function prints a message with a divider above and below the message.

    Args:
        message (str): Message to be printed
        top (bool): Print divider above message
        bottom (bool): Print divider below message
        divider (str): Divider to be used

    Returns:
        None

    Example:
        _print_message_section("This is a message", top=True, bottom=True, divider="=")

    Output:
        ===================
        This is a message
        ===================

    Example:
        _print_message_section("This is a message", top=True, bottom=False, divider="*")

    Output:
        ******************
        This is a message

    """
    if top:
        logging.info(divider * len(message))
    logging.info(message)
    if bottom:
        logging.info(divider * len(message))


def _create_log_file(log_path):
    """Create Log File

    This function creates the log file if it does not exist and handles Windows vs Linux pathing.

    Args:
        log_path (str): Path to log file

    Returns:
        str: Path to log file
    """
    try:
        # logging.debug("Function: create_log_file")

        # Split the path into directory and file name
        # Handle if ~ is passed as the log file location
        log_path = os.path.expanduser(log_path)

        # If OS is Windows, replace \ with / to avoid errors
        if os.name == 'nt':
            log_path = path.replace('/', '\\')

        # Split the path into directory and file name
        # filename = os.path.basename(path)
        directory = os.path.dirname(log_path)

        # Test if the directory exists
        if not os.path.exists(directory):
            print("Creating directory: {0}".format(directory))
            os.makedirs(directory)

        # Test if the file exists
        if not os.path.exists(log_path):
            print("Creating file: {0}".format(log_path))
            open(log_path, 'a').close()

        # logging.debug("Returning: {}".format(log_path))
        # logging.debug("Function: create_log_file completed")

        # Return the path
        return log_path


    except Exception as e:
        logging.error("An error occurred in create_log_file: {}".format(e))
        sys.exit(1)


def _parse_args (args=None):
    """Handle command line arguments

    This function processes the command line arguments passed to the module.

    Args:
        sys.argv[1:]: Arguments passed from command line referenced as sys.argv[1:]

    Returns:
        list_only (bool): List entities that would be created and exit without creating them (dry run)
        aws_profile (str): AWS Profile to be used
        region (str): AWS Region to be used
        bucket_name (str): S3 Bucket Name to be used
        bucket_region (str): S3 Bucket Region to be used
        bucket_versioning (bool): S3 Bucket Versioning to be used
        bucket_encryption (bool): S3 Bucket Encryption to be used
        bucket_kms_key_id (str): S3 Bucket KMS Key ID to be used
        bucket_public_access_block (bool): S3 Bucket Public Access Block to be used
        dynamodb_table_enabled (bool): Enable DynamoDB Table to be used
        dynamodb_table_name (str): DynamoDB Table Name to be used
        dynamodb_table_region (str): DynamoDB Table Region to be used
        dynamodb_table_read_capacity (int): DynamoDB Table Read Capacity to be used
        dynamodb_table_write_capacity (int): DynamoDB Table Write Capacity to be used
        log_file (str): Log file to be used
        log_level (str): Log level to be used
    """
    try:
        # logging.debug("Function: parse_args")

        all_args = argparse.ArgumentParser(description='Terrform Remote Backend Bootstrap v{}'.format(version), formatter_class=argparse.RawTextHelpFormatter)

        connection_group = all_args.add_argument_group('AWS Connection Details')
        connection_group.add_argument('--aws-profile', '-a', required=False, default='default', help='AWS Profile: default = default (Example: -a vcra-prod)', type=str)
        connection_group.add_argument('--region', '-r', required=False, default='us-east-1',help="AWS Region: default = us-east-1 (Example: -r eu-west-2)", type=str)

        bucket_group = all_args.add_argument_group('S3 Bucket Details')
        bucket_group.add_argument('--bucket-name', '-bn', required=False, default='terraform-remote-state', help='S3 Bucket Name: default = terraform-remote-state (Example: -bn terraform-remote-state)', type=str)
        bucket_group.add_argument('--bucket-region', '-br', required=False, help='S3 Bucket Region: default = <same as AWS connection region> (Example: -br us-east-1)', type=str)
        bucket_group.add_argument('--bucket-versioning', '-bv', required=False, default=True, help='S3 Bucket Versioning: default = True (Example: -bv False)', type=bool)
        bucket_group.add_argument('--bucket-encryption', '-be', required=False, default=True, help='S3 Bucket Encryption: default = True (Example: -be False)', type=bool)
        bucket_group.add_argument('--bucket-kms-key-id', '-bk', required=False, help='S3 Bucket KMS Key ID: default = <none> (Example: -bk 1234-5678-9012-3456-7890)', type=str)
        bucket_group.add_argument('--bucket-public-access-block', '-bpb', required=False, default=True, help='S3 Bucket Public Access Block: default = True (Example: -bpb False)', type=bool)

        dynamodb_group = all_args.add_argument_group('DynamoDB Table Details')
        dynamodb_group.add_argument('--dynamodb-table-enabled', '-ddb', required=False, default=True, help='DynamoDB Table Enabled: default = True (Example: -ddb False)', type=bool)
        dynamodb_group.add_argument('--dynamodb-table-name', '-dt', required=False, default='terraform-remote-state', help='DynamoDB Table Name: default = terraform-remote-state (Example: -dt terraform-remote-state)', type=str)
        dynamodb_group.add_argument('--dynamodb-table-region', '-dr', required=False, help='DynamoDB Table Region: default = <same as AWS connection region> (Example: -dr us-east-1)', type=str)
        dynamodb_group.add_argument('--dynamodb-table-read-capacity', '-drc', required=False, default=5, help='DynamoDB Table Read Capacity: default = 5 (Example: -drc 5)', type=int)
        dynamodb_group.add_argument('--dynamodb-table-write-capacity', '-dwc', required=False, default=5, help='DynamoDB Table Write Capacity: default = 5 (Example: -dwc 5)', type=int)
        # dynamodb_group.add_argument('--dynamodb-billing-mode', '-dbm', required=False, default='PROVISIONED', help='DynamoDB Billing Mode: default = PROVISIONED (Example: -dbm PROVISIONED)', type=str)
        # dynamodb_group.add_argument('--dynamodb-table-encryption', '-de', required=False, default='AES256', help='DynamoDB Table Encryption: default = AES256 (Example: -de AES256)', type=str)
        # dynamodb_group.add_argument('--dynamodb-table-kms-key-id', '-dk', required=False, help='DynamoDB Table KMS Key ID: default = <none> (Example: -dk 1234-5678-9012-3456-7890)', type=str)

        log_group = all_args.add_argument_group('Log Options')
        log_group.add_argument('--log-file', '-l', required=False, help='Log file location (Example: -l /tmp/createAMI.log)', type=str)
        log_group.add_argument('--log-level', '-ll', required=False, default='INFO', help='Log level: default = INFO (Example: -ll DEBUG)', type=str)

        options_group = all_args.add_argument_group('Options')
        options_group.add_argument('--list-only', '-lo','--dry-run','--check','-C', required=False, action='store_true', help='[Flag] Dry run to list entities that would be created and exit without creating')

        args=all_args.parse_args()

        # Parse passed arguments and update logging variables if needed
        global log_level # Update global log_level variable
        global logging_file # Update global log_file variable

        # Parse passed arguments and update logging variables if needed
        for key, value in vars(args).items():
            if (key == 'log_file' and not value is None):
                # Pass to create_log_file function
                logging_file = _create_log_file(value)
            if (key == 'log_file' and value is None): # If OS is Windows update /dev/null to NUL
                if os.name == 'nt':
                    logging_file = 'NUL'
            if key == 'log_level':
                log_level=value.upper()

        # logging.debug("Returned args: {}".format(args))
        # logging.debug("Function: _parse_args() completed")

        return args

    except Exception as e:
        logging.error('Error parsing arguments: {}'.format(e))
        sys.exit(1)


def _configure_logging():
    """Configure logging

    This function configures the logging module to write to a file and stdout and with the specified log level and format.

    Args:
        None

    Returns:
        None
    """

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(logging_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def _aws_connect(aws_profile, region):
    """Connect to AWS

    This function connects to AWS using the AWS CLI credentials or AWS Session Token and creates a boto3 session.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()

    Returns:
        None
    """
    try:
        # logging.debug("Function: _aws_connect() started")

        logging.info("Connecting to AWS")

        # Test if AWS CLI credentials are configured and that the passed profile exists by using _check_aws_profile() and looking for a 0 return code, if a 0 return code is found use the profile and region passed to the script to create a boto3 session
        if _check_aws_profile(aws_profile) == 0:
            aws_session = boto3.Session(profile_name=aws_profile,region_name=region)
            # Print AWS Session Details using _print_aws_session_details() and then return to main()
            _print_aws_session_details(aws_session)
            # logging.debug("Function: _aws_connect() completed")
            return aws_session
        # Test if AWS Session Token is set in the environment and if so use them to create a boto3 session
        if _check_aws_vars() == 0:
            aws_session = boto3.Session()
            # Print AWS Session Details using _print_aws_session_details() and then return to main()
            _print_aws_session_details(aws_session)
            # logging.debug("Function: _aws_connect() completed")
            return aws_session

        # If neither the passed profile or AWS Session Token are set in the environment then exit with an error
        logging.error("AWS CLI credentials are not configured or the profile passed does not exist")
        logging.warning("Please configure AWS CLI credentials or set AWS Session Tokens in the environment variables")
        sys.exit(1)

    except ClientError as e:
        logging.error("Error in _aws_connect: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _aws_connect: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _print_aws_session_details(aws_session):
    """Print AWS Session Details

    This function prints the AWS Session details to stdout.

    Args:
        aws_session (boto3.session.Session): AWS Session

    Returns:
        None
    """
    try:
        # logging.debug("Function: _print_aws_session_details() started")

        _print_message_section("AWS Session Details:", top=False, bottom=False)

        logging.info("Profile: {0}".format(aws_session.profile_name))
        logging.info("Region: {0}".format(aws_session.region_name))
        logging.info("User: {0}".format(aws_session.client('sts').get_caller_identity().get('Arn')))
        logging.debug("AWS Session: {0}".format(aws_session))

        _print_message_section("Connected to AWS", top=False, bottom=False)

        # logging.debug("Function: _print_aws_session_details() completed")

    except ClientError as e:
        logging.error("Error in _print_aws_session_details: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _print_aws_session_details: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _check_aws_profile(aws_profile):
    """Check if the passed AWS Profile exists

    This function checks if the passed AWS Profile exists in the AWS CLI credentials file.

    Args:
        aws_profile (str): AWS Profile

    Returns:
        int: 0 if the AWS Profile exists, 1 if the AWS Profile does not exist

    """
    # Check if AWS CLI credentials are configured and that the passed profile exists
    try:
        # logging.debug("Function: _check_aws_profile() started")

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

        if aws_profile in aws_profiles:
            logging.info("AWS CLI credentials are configured and profile {0} exists".format(aws_profile))
            # _print_message_section("AWS CLI credentials are configured and profile {0} exists".format(args.aws_profile), top=False, bottom=True)
            # logging.debug("Function: _check_aws_profile() completed")
            return 0
        else:
            logging.error("AWS CLI credentials are not configured or profile {0} does not exist".format(aws_profile))
            # _print_message_section("AWS CLI credentials are not configured or profile {0} does not exist".format(args.aws_profile), top=False, bottom=True)
            # logging.debug("Function: _check_aws_profile() completed")
            return 1

    except ClientError as e:
        logging.error("Error in _check_aws_profile: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _check_aws_profile: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


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
            # logging.debug("Function: _check_aws_vars() completed")
            return 1
        if environ.get('AWS_SECRET_ACCESS_KEY') is None:
            logging.error("AWS_SECRET_ACCESS_KEY is not set")
            logging.debug("Function: _check_aws_vars() completed")
            return 1
        if environ.get('AWS_SESSION_TOKEN') is None:
            logging.warning("AWS_SESSION_TOKEN is not set, ensure that the configured AWS User does not require MFA")
            # logging.debug("Function: _check_aws_vars() completed")
            return 0
        # If all variables are set then return 0
        logging.info("AWS variables are set")
        # logging.debug("Function: _check_aws_vars() completed")
        return 0

    except ClientError as e:
        logging.error("Error in _check_aws_vars: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _check_aws_vars: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _print_args(args):
    """Print arguments passed from command line

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()

    Returns:
        None
    """
    # logging.debug("Function: _print_args() started")

    _print_message_section("Supplied Arguments", top=False, bottom=True)

    for key, value in vars(args).items():
        # Replace _ with space and capitalize first letter of each word
        key = key.replace("_"," ").title()
        logging.info('{0} : {1}'.format(key, value))

    logging.info("===================")

    # logging.debug("Function: _print_args() completed")


def _lookup_aws_account_id(aws_session):
    """Lookup AWS Account ID

    This function looks up the AWS Account ID using the AWS Session.

    Args:
        aws_session (_type_): _description_

    Returns:
        str: AWS Account ID
    """
    try:
        # logging.debug("Function: _lookup_aws_account_id() started")

        logging.debug("Looking up AWS Account ID")

        aws_account_id = aws_session.client('sts').get_caller_identity().get('Account')

        logging.debug("Returned AWS Account ID: {0}".format(aws_account_id))
        # logging.debug("Function: _lookup_aws_account_id() completed")

        return aws_account_id

    except ClientError as e:
        logging.error("Error in _lookup_aws_account_id: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _lookup_aws_account_id: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _check_existing_s3_bucket(s3_client, bucket_name):
    """Check if an S3 Bucket already exists

    This function checks if an S3 Bucket matching the required configuration already exists.

    Args:
        args (_type_): _description_
        aws_account_id (_type_): _description_
        aws_session (_type_): _description_
    """
    try:
        # logging.debug("Function: _check_existing_s3_bucket() started")
        logging.info("Checking if S3 Bucket {0} already exists".format(bucket_name))

        # Check if s3 bucket exists
        if s3_client.head_bucket(Bucket=bucket_name):
            logging.debug("S3 Bucket {0} already exists".format(bucket_name))
            return True
        else:
            logging.debug("S3 Bucket {0} does not exist".format(bucket_name))
            return False

        # # Check if s3 bucket exists
        # if s3_client(bucket_name).creation_date is None:
        #     logging.debug("S3 Bucket {0} does not exist".format(bucket_name))
        #     return False
        # else:
        #     logging.debug("S3 Bucket {0} already exists".format(bucket_name))
        #     return True

    except ClientError as e:
        if e.response['Error']['Code'] == '301':
            logging.error("[301] S3 Bucket {0} is redirected and may already exist in another account".format(bucket_name))
            sys.exit(1)
        if e.response['Error']['Code'] == '403':
            logging.error("[403] Private Bucket.  Forbidden access to S3 Bucket {0}, may exist in another account".format(bucket_name))
            sys.exit(1)
        if e.response['Error']['Code'] == '404':
            logging.info("[404] S3 Bucket {0} does not exist".format(bucket_name))
            return False
        logging.error("Error in _check_existing_s3_bucket: {0}".format(e))
        sys.exit(1)
    except TypeError as e:
        logging.error("Error in _check_existing_s3_bucket: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _check_existing_s3_bucket: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _store_s3_bucket_details(bucket_name, bucket_region, bucket_kms_key_id, bucket_encryption, kms_key_id, kms_key_alias):
    """Store S3 Bucket details in DynamoDB

    This function stores the S3 Bucket details ready to be displayed at the end of the script.

    Args:
        bucket_name (str): S3 Bucket name
        bucket_region (str): S3 Bucket region
        bucket_kms_key_id (str): KMS Key ID
        bucket_encryption (bool): S3 Bucket encryption
        kms_key_id (str): KMS Key ID

    Returns:
        s3_bucket_name (str): S3 Bucket name
        s3_bucket_region (str): S3 Bucket region
        s3_kms_key_id (str): KMS Key ID
    """
    try:
        # Declare global variables to be updated in this function
        global s3_bucket_name
        global s3_bucket_region
        global s3_kms_key_id
        global s3_kms_key_alias

        # Store the S3 Bucket name in the global variable s3_bucket_name
        s3_bucket_name = bucket_name
        # Store the S3 Bucket region in the global variable s3_bucket_region
        s3_bucket_region = bucket_region
        # Store the KMS key ID in the global variable kms_key_id if it was created
        if bucket_kms_key_id is None and bucket_encryption is True:
            s3_kms_key_id = kms_key_id
        else:
            s3_kms_key_id = bucket_kms_key_id
        # Store KMS key alias in the global variable s3_kms_key_alias
        s3_kms_key_alias = kms_key_alias
        return

    except ClientError as e:
        logging.error("Error in _store_s3_bucket_details: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _store_s3_bucket_details: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _create_s3_bucket(args, aws_account_id, aws_session):
    """Create an S3 Bucket based on the passed arguments

    This function creates an S3 Bucket based on the passed arguments.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()
        aws_account_id (str): AWS Account ID
        aws_session (session): AWS Session

    Returns:
        s3_bucket_name (str): Name of the S3 Bucket
        s3_bucket_region (str): Region of the S3 Bucket
        kms_key_id (str): KMS Key ID
    """
    try:
        # logging.debug("Function: _create_s3_bucket() started")

        # Create an S3 client from scratch not using the existing aws_session
        s3_client = boto3.client('s3', region_name=args.bucket_region)

        # Use the global variable aws_session to create an S3 client specifying the S3 region
        # s3_client = aws_session.client('s3', region_name=args.bucket_region)
        # s3_client = aws_session.client('s3')
        # Disable auto-redirection of requests to another region
        deq = s3_client.meta.events._emitter._handlers.prefix_search('needs-retry.s3')
        while len(deq) > 0:
            s3_client.meta.events.unregister('needs-retry.s3', handler=deq.pop())

        # Continue with creating the S3 Bucket if it does not exist
        # Check if a region was passed and if not set the region to the region of the AWS Session
        if args.bucket_region is None:
            args.bucket_region = aws_session.region_name

        # Append AWS Account ID to the bucket name to ensure it is unique
        args.bucket_name = '{0}-{1}'.format(args.bucket_name, aws_account_id)

        # Create configuration for the S3 Bucket based on the passed arguments for versioning, encryption, kms key, and bucket policy
        bucket_config = {}
        if args.bucket_versioning is True:
            bucket_config['VersioningConfiguration'] = {'Status': 'Enabled'}
        if args.bucket_encryption is True:
            bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}

        # Create a KMS Client session
        kms_client = aws_session.client('kms')

        # Open variable for kms_key_id
        kms_key_id = None

        # Prepare an alias for the KMS Key
        kms_key_alias = 'alias/{0}'.format(args.bucket_name)

        # Check if the KMS Key ID already exists
        if args.bucket_kms_key_id is None and args.bucket_encryption is True:
            # Check if the KMS Key Alias already exists
            keys_list = kms_client.list_keys()
            key_exists = False
            for key in keys_list['Keys']:
                key_id = key['KeyId']
                key_aliases = kms_client.list_aliases(KeyId=key_id)
                for key_alias in key_aliases['Aliases']:
                    if key_alias['AliasName'] == kms_key_alias:
                        kms_key_id = key_id
                        key_exists = True
                        logging.debug("KMS Key ID {0} already exists".format(kms_key_id))
                        bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': kms_key_id}}]}
                        break
                if key_exists is True: # Break out of the for loop if the key exists
                    break

        # If list_only is True log what what we would do if the key does not already exist
        if key_exists is not True and args.bucket_encryption is True and args.list_only is True:
            logging.info("KMS Key ID {0} does not exist, would create KMS Key ID {0}".format(kms_key_alias))

        # Create key
        if key_exists is not True and args.bucket_encryption is True and args.list_only is False:
            create_key = True
            # kms_key = kms_client.create_key()
            # kms_key_id = kms_key['KeyMetadata']['KeyId']
            # kms_client.create_alias(AliasName=kms_key_alias, TargetKeyId=kms_key_id)
            # bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': kms_key_id}}]}

        # If a KMS key was passed and encryption is enabled then use the passed KMS key
        if args.bucket_kms_key_id is not None and args.bucket_encryption is True:
            bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': args.bucket_kms_key}}]}

        # Create a bucket policy for the S3 Bucket based on the bucket_public_access_block true/false
        bucket_policy = {}
        if args.bucket_public_access_block is True:
            bucket_policy['PublicAccessBlockConfiguration'] = {'BlockPublicAcls': True, 'BlockPublicPolicy': True, 'IgnorePublicAcls': True, 'RestrictPublicBuckets': True}
        if args.bucket_public_access_block is False:
            bucket_policy['PublicAccessBlockConfiguration'] = {'BlockPublicAcls': False, 'BlockPublicPolicy': False, 'IgnorePublicAcls': False, 'RestrictPublicBuckets': False}

        # Display the bucket configuration
        _print_message_section("S3 Bucket Configuration", top=True, bottom=True)
        logging.info("Bucket Name: {0}".format(args.bucket_name))
        logging.info("Bucket Region: {0}".format(args.bucket_region))
        logging.info("Bucket KMS Key ID: {0}".format(args.bucket_kms_key_id))
        logging.info("Bucket KMS Key Alias: {0}".format(kms_key_alias))
        # Log bucket configuration
        if bucket_config:
            logging.info("Bucket Configuration: {0}".format(bucket_config))
        # Log bucket policy
        if bucket_policy:
            logging.info("Bucket Policy: {0}".format(bucket_policy))
        logging.info("===================")

        # Check if the S3 Bucket already exists and if it does store details and return
        if _check_existing_s3_bucket(s3_client, args.bucket_name) is True:
            logging.info("S3 Bucket {0} already exists".format(args.bucket_name))
            # Store the S3 Bucket details
            _store_s3_bucket_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)
            return

        if args.list_only is True:
            logging.warning("List-only/dry-run is set, not creating S3 Bucket")
            _store_s3_bucket_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)
            return

        # If list-only/dry-run is not set and the bucket doesn't already exist then create the S3 Bucket and key
        if create_key is True:
            kms_key = kms_client.create_key()
            kms_key_id = kms_key['KeyMetadata']['KeyId']
            kms_client.create_alias(AliasName=kms_key_alias, TargetKeyId=kms_key_id)
            bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': kms_key_id}}]}
        # Create the S3 Bucket
        s3_client.create_bucket(Bucket=args.bucket_name, CreateBucketConfiguration={'LocationConstraint': args.bucket_region})
        # If the bucket_config is not empty then set the configuration for the S3 Bucket
        if bucket_config:
            s3_client.put_bucket_versioning(Bucket=args.bucket_name, VersioningConfiguration=bucket_config['VersioningConfiguration'])
            s3_client.put_bucket_encryption(Bucket=args.bucket_name, ServerSideEncryptionConfiguration=bucket_config['ServerSideEncryptionConfiguration'])
        # If the bucket_policy is not empty then set the policy for the S3 Bucket
        if bucket_policy:
            s3_client.put_public_access_block(Bucket=args.bucket_name, PublicAccessBlockConfiguration=bucket_policy['PublicAccessBlockConfiguration'])

        # Store the S3 Bucket details
        _store_s3_bucket_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)

        # logging.debug("Function: _create_s3_bucket() completed")

    except AttributeError as e:
        logging.error("Error in _create_s3_bucket: {0}".format(e))
        sys.exit(1)
    except ClientError as e:
        logging.error("Error in _create_s3_bucket: {0}".format(e))
        sys.exit(1)
    except TypeError as e:
        logging.error("Error in _create_s3_bucket: {0}".format(e))
        sys.exit(1)
    except UnboundLocalError as e:
        logging.error("Error in _create_s3_bucket: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _create_s3_bucket: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _check_existing_dynamodb_table(dynamodb_client, dynamodb_table_name):
    """Check if a DynamoDB Table already exists

    This function checks if a DynamoDB Table already exists.

    Args:
        dynamodb_client (obj): Boto3 DynamoDB client object
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        table_exists (bool): True if the DynamoDB Table exists, False if it does not exist
    """
    try:
        # logging.debug("Function _check_existing_dynamodb_table called with dynamodb_table_name: {0}".format(dynamodb_table_name))

        logging.info("Checking if DynamoDB Table {0} already exists".format(dynamodb_table_name))

        # Check if the DynamoDB Table already exists
        table_exists = False
        for table in dynamodb_client.list_tables()['TableNames']:
            if table == dynamodb_table_name:
                logging.debug("DynamoDB Table {0} already exists".format(dynamodb_table_name))
                table_exists = True
                break

        # logging.debug("Function: _check_existing_dynamodb_table() completed")

        return table_exists

    except AttributeError as e:
        logging.error("Error in _check_existing_dynamodb_table: {0}".format(e))
        sys.exit(1)
    except ClientError as e:
        logging.error("Error in _check_existing_dynamodb_table: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _check_existing_dynamodb_table: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _store_dynamodb_table_details(dynamodb_table_name):
    """Store the DynamoDB Table details

    This function stores the DynamoDB Table details.

    Args:
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        dynamodb_table (str): Name of the DynamoDB Table
    """
    try:
        # logging.debug("Function _store_dynamodb_table_details called with dynamodb_table_name: {0} and dynamodb_table_region: {1}".format(dynamodb_table_name, dynamodb_table_region))

        # Declare global variables to be updated in this function
        global dynamodb_table # Store the DynamoDB Table details
        dynamodb_table = dynamodb_table_name

        # logging.debug("Function: _store_dynamodb_table_details() completed")

    except AttributeError as e:
        logging.error("Error in _store_dynamodb_table_details: {0}".format(e))
        sys.exit(1)
    except ClientError as e:
        logging.error("Error in _store_dynamodb_table_details: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _store_dynamodb_table_details: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _create_dynamodb_table(args, aws_account_id, aws_session):
    """Create a DynamoDB Table based on the passed arguments

    This function creates a DynamoDB Table based on the passed arguments.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()

    Returns:
        dynamodb_table_name (str): Name of the DynamoDB Table
    """
    try:
        # logging.debug("Function _create_dynamodb_table called with args: {0}".format(args))

        # Append the AWS Account ID to the DynamoDB Table name to ensure it is unique
        args.dynamodb_table_name = '{0}-{1}'.format(args.dynamodb_table_name, aws_account_id)

        # If the DynamoDB Table region is not passed then use the region of the AWS Account
        if args.dynamodb_table_region is None:
            args.dynamodb_table_region = aws_session.region_name

        _print_message_section("DynamoDB Table Configuration", top=True, bottom=True)
        logging.info("DynamoDB Table Name: {0}".format(args.dynamodb_table_name))
        logging.info("DynamoDB Table Region: {0}".format(args.dynamodb_table_region))
        logging.info("DynamoDB Table Read Capacity: {0}".format(args.dynamodb_table_read_capacity))
        logging.info("DynamoDB Table Write Capacity: {0}".format(args.dynamodb_table_write_capacity))
        logging.info("DynamoDB Primary Key: {0}".format("LockID"))
        logging.info("========================================")

        # Create a DynamoDB client based on the passed dynamodb_table_region
        dynamodb_client = aws_session.client('dynamodb', region_name=args.dynamodb_table_region)

        # Check if the DynamoDB Table already exists
        if _check_existing_dynamodb_table(dynamodb_client, args.dynamodb_table_name) is True:
            logging.info("DynamoDB Table {0} already exists".format(args.dynamodb_table_name))
            _store_dynamodb_table_details(args.dynamodb_table_name)
            return

        # If list-only/dry-run is set then exit after printing the configuration
        if args.list_only is True:
            # Store the DynamoDB Table name in the global variable dynamodb_table_name
            _store_dynamodb_table_details(args.dynamodb_table_name)
            logging.warning("--list-only/dry-run no DynamoDB Table was created")
            # logging.debug("Function: _create_dynamodb_table() completed")
            return

        # If list-only/dry-run is not set then create the DynamoDB Table
        # based on passed dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity, dynamodb_table_write_capacity arguments create a DynamoDB Table with a primary key of LockID
        dynamodb_client.create_table(TableName=args.dynamodb_table_name, AttributeDefinitions=[{'AttributeName': 'LockID', 'AttributeType': 'S'}], KeySchema=[{'AttributeName': 'LockID', 'KeyType': 'HASH'}], ProvisionedThroughput={'ReadCapacityUnits': args.dynamodb_table_read_capacity, 'WriteCapacityUnits': args.dynamodb_table_write_capacity}, BillingMode='PROVISIONED')

        # Store the DynamoDB Table name in the global variable dynamodb_table
        _store_dynamodb_table_details(args.dynamodb_table_name)

        # logging.debug("Exiting Function _create_dynamodb_table with dynamodb_table_name: {0}".format(dynamodb_table_name))

    except ClientError as e:
        logging.error("Error in _create_dynamodb_table: {0}".format(e))
        sys.exit(1)
    except TypeError as e:
        logging.error("Error in _create_dynamodb_table: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in _create_dynamodb_table: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


def _print_s3_and_dynamodb_backend_details():
    """Print S3 and DynamoDB Backend Details

    This function prints the S3 and DynamoDB Backend Details.

    Args:
        None

    Returns:
        None
    """
    try:
        # logging.debug("Function: _print_s3_and_dynamodb_backend_details")

        _print_message_section('S3 and DynamoDB Backend Details', top=True, bottom=False, divider='*')
        _print_message_section('Add the configuration below to your Terraform configuration!', top=False, bottom=True, divider='*')

        logging.info("S3 Bucket Name: {0}".format(s3_bucket_name))
        logging.info("S3 Bucket Region: {0}".format(s3_bucket_region))
        if s3_kms_key_id is not None:
            logging.info("KMS Key ID: {0}".format(s3_kms_key_id))
        if s3_kms_key_alias is not None:
            logging.info("KMS Key Alias: {0}".format(s3_kms_key_alias))
        if dynamodb_table is not None:
            logging.info("DynamoDB Table Name: {0}".format(dynamodb_table))

        # logging.debug("Exiting Function: _print_s3_and_dynamodb_backend_details")

    except:
        logging.error("Unexpected error in _print_s3_and_dynamodb_backend_details: {0}".format(sys.exc_info()[0]))
        sys.exit(1)


# Function to call when used as a module
def create_s3_backend():
    """Create S3 Backend

    This function is called when the module is used as a module and not as a script.

    Args:
        None

    Returns:
        None
    """
    _main(sys.argv[1:]) # Call main function and pass any arguments
    return s3_bucket_name, s3_bucket_region, s3_kms_key_id, dynamodb_table_name

if __name__ == "__main__":
    _main(sys.argv[1:]) # Call main function and pass any arguments