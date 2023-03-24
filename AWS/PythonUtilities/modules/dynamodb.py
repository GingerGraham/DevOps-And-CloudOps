#!/usr/bin/env python3

"""DynamoDB utilities
"""


# Import global modules
import logging

# Import local modules
import modules.output as output

# Import third-party modules
from botocore.exceptions import ClientError


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
        logging.debug("Function _check_existing_dynamodb_table called with arguments: dynamodb_client={0}, dynamodb_table_name={1}".format(dynamodb_client, dynamodb_table_name))

        logging.info("Checking if DynamoDB Table {0} already exists".format(dynamodb_table_name))

        # Check if the DynamoDB Table already exists
        table_exists = False
        for table in dynamodb_client.list_tables()['TableNames']:
            if table == dynamodb_table_name:
                logging.debug("DynamoDB Table {0} already exists".format(dynamodb_table_name))
                table_exists = True
                break

        logging.debug("Function: _check_existing_dynamodb_table() completed")

        return table_exists

    except AttributeError as e:
        logging.error("Error in _check_existing_dynamodb_table: {0}".format(e))
        return 1
    except ClientError as e:
        logging.error("Error in _check_existing_dynamodb_table: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _check_existing_dynamodb_table: {0}".format(sys.exc_info()[0]))
        return 1


def _store_dynamodb_table_details(dynamodb_table_name):
    """Store the DynamoDB Table details

    This function stores the DynamoDB Table details.

    Args:
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        dynamodb_table (str): Name of the DynamoDB Table
    """
    try:
        logging.debug("Function _store_dynamodb_table_details called with arguments: dynamodb_table_name={0}".format(dynamodb_table_name))

        # Declare global variables to be updated in this function
        global dynamodb_table # Store the DynamoDB Table details
        dynamodb_table = dynamodb_table_name

        logging.debug("Function: _store_dynamodb_table_details() completed")

    except AttributeError as e:
        logging.error("Error in _store_dynamodb_table_details: {0}".format(e))
        return 1
    except ClientError as e:
        logging.error("Error in _store_dynamodb_table_details: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _store_dynamodb_table_details: {0}".format(sys.exc_info()[0]))
        return 1


def _create_dynamodb_table(args, aws_account_id, aws_session):
    """Create a DynamoDB Table based on the passed arguments

    This function creates a DynamoDB Table based on the passed arguments.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()

    Returns:
        dynamodb_table_name (str): Name of the DynamoDB Table
    """
    try:
        logging.debug("Function _create_dynamodb_table called with arguments: args={0}, aws_account_id={1}, aws_session={2}".format(args, aws_account_id, aws_session))

        # Append the AWS Account ID to the DynamoDB Table name to ensure it is unique
        args.dynamodb_table_name = '{0}-{1}'.format(args.dynamodb_table_name, aws_account_id)

        # If the DynamoDB Table region is not passed then use the region of the AWS Account
        if args.dynamodb_table_region is None:
            args.dynamodb_table_region = aws_session.region_name

        output.log_message_section("DynamoDB Table Configuration", top=True, bottom=True)
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
            logging.debug("Function: _create_dynamodb_table() completed")
            return

        # If list-only/dry-run is set then exit after printing the configuration
        if args.list_only is True:
            # Store the DynamoDB Table name in the global variable dynamodb_table_name
            _store_dynamodb_table_details(args.dynamodb_table_name)
            logging.warning("--list-only/dry-run no DynamoDB Table was created")
            logging.debug("Function: _create_dynamodb_table() completed")
            return

        # If list-only/dry-run is not set then create the DynamoDB Table
        # based on passed dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity, dynamodb_table_write_capacity arguments create a DynamoDB Table with a primary key of LockID
        dynamodb_client.create_table(TableName=args.dynamodb_table_name, AttributeDefinitions=[{'AttributeName': 'LockID', 'AttributeType': 'S'}], KeySchema=[{'AttributeName': 'LockID', 'KeyType': 'HASH'}], ProvisionedThroughput={'ReadCapacityUnits': args.dynamodb_table_read_capacity, 'WriteCapacityUnits': args.dynamodb_table_write_capacity}, BillingMode='PROVISIONED')

        # Store the DynamoDB Table name in the global variable dynamodb_table
        _store_dynamodb_table_details(args.dynamodb_table_name)

        logging.debug("Exiting Function _create_dynamodb_table with dynamodb_table_name: {0}".format(dynamodb_table_name))

    except ClientError as e:
        logging.error("Error in _create_dynamodb_table: {0}".format(e))
        return 1
    except TypeError as e:
        logging.error("Error in _create_dynamodb_table: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _create_dynamodb_table: {0}".format(sys.exc_info()[0]))
        return 1


def _print_s3_and_dynamodb_backend_details():
    """Print S3 and DynamoDB Backend Details

    This function prints the S3 and DynamoDB Backend Details.

    Args:
        None

    Returns:
        None
    """
    try:
        logging.debug("Function: _print_s3_and_dynamodb_backend_details")

        output.log_message_section('S3 and DynamoDB Backend Details', top=True, bottom=False, divider='*')
        output.log_message_section('Add the configuration below to your Terraform configuration!', top=False, bottom=True, divider='*')

        logging.info("S3 Bucket Name: {0}".format(s3_bucket_name))
        logging.info("S3 Bucket Region: {0}".format(s3_bucket_region))
        if s3_kms_key_id is not None:
            logging.info("KMS Key ID: {0}".format(s3_kms_key_id))
        if s3_kms_key_arn is not None:
            logging.info("KMS Key ARN: {0}".format(s3_kms_key_arn))
        if s3_kms_key_alias is not None:
            logging.info("KMS Key Alias: {0}".format(s3_kms_key_alias))
        if dynamodb_table is not None:
            logging.info("DynamoDB Table Name: {0}".format(dynamodb_table))

        logging.debug("Exiting Function: _print_s3_and_dynamodb_backend_details")

    except NameError as e:
        logging.error("Error in _print_s3_and_dynamodb_backend_details: {0}".format(e))
        return 1
    except:
        logging.error("Unexpected error in _print_s3_and_dynamodb_backend_details: {0}".format(sys.exc_info()[0]))
        return 1