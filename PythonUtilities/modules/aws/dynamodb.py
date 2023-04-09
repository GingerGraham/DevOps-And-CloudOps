#!/usr/bin/env python3

"""DynamoDB utilities

This module contains functions to interact with DynamoDB.

Author: Graham Watts
Date: 2023-04-03
Version: 1.0.0

Functions:

    check_existing_dynamodb_table(aws_session, dynamodb_table_name, dynamodb_table_region)
    create_dynamodb_table(aws_account_id, aws_session, dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity=5, dynamodb_table_write_capacity=5, dynamodb_table_attributes=[], dynamodb_table_key_schema=[], dynamodb_table_billing_mode="PROVISIONED", dry_run=False)
    print_dynamodb_table_details(aws_session, dynamodb_table_name, dynamodb_table_region)

"""


# Import global modules
import logging
import sys

# Import local modules
import modules.output as output
import modules.aws.connect as aws_connect

# Import third-party modules
from botocore.exceptions import ClientError, ParamValidationError


def check_existing_dynamodb_table(aws_session=None, dynamodb_client=None, dynamodb_table_arn=None, dynamodb_table_name=None, dynamodb_table_region=None):
    """Check if a DynamoDB Table already exists

    This function checks if a DynamoDB Table already exists.

    Args:
        aws_session (obj): Boto3 session object - not required if dynamodb_client is provided instead
        dynamodb_client (obj): Boto3 DynamoDB client object - not required if aws_session is provided instead
        dynamodb_table_arn (str): ARN of the DynamoDB Table - not required if dynamodb_table_name and dynamodb_table_region are provided instead
        dynamodb_table_name (str): Name of the DynamoDB Table
        dynamodb_table_region (str): Region of the DynamoDB Table

    Returns:
        dynamodb_table_arn (str): ARN of the DynamoDB Table
        False (bool): False if the DynamoDB Table does not exist
    """
    try:
        logging.debug(f"Function check_existing_dynamodb_table called with arguments: aws_session={aws_session}, dynamodb_table_name={dynamodb_table_name}, dynamodb_table_region={dynamodb_table_region}")

        logging.info(f"Checking if DynamoDB Table {dynamodb_table_name} already exists")

        # Check if both aws_session and dynamodb_client are None and if so exit with an error
        if aws_session == None and dynamodb_client == None:
            logging.error("Error: Both aws_session and dynamodb_client are None")
            return 1

        if dynamodb_client == None:
            dynamodb_client = aws_connect.session_connect(aws_session=aws_session, region=dynamodb_table_region, client_type="dynamodb")

        if dynamodb_client == 1:
            logging.error("Error creating DynamoDB client")
            logging.debug("Function: _check_existing_dynamodb_table() completed")
            return 1

        # If the dynamodb_table_region is None then set it to the region of the dynamodb_client
        if dynamodb_table_region == None:
            dynamodb_table_region = dynamodb_client.meta.region_name

        # Check if table name or region are None and if so exit with an error
        if dynamodb_table_name == None and dynamodb_table_arn == None:
            logging.error("Error: Both dynamodb_table_name and dynamodb_table_arn are None")
            return 1

        if dynamodb_table_arn != None:
            dynamodb_table_arn = _check_existing_dynamodb_table_arn(dynamodb_client=dynamodb_client, dynamodb_table_arn=dynamodb_table_arn)

        if dynamodb_table_name != None and (dynamodb_table_arn == None or dynamodb_table_arn == False or dynamodb_table_arn == 1):
            dynamodb_table_arn = _check_existing_dynamodb_table_name(dynamodb_client=dynamodb_client, dynamodb_table_name=dynamodb_table_name)

        if dynamodb_table_arn == 1:
            logging.error("Error checking DynamoDB Table")
            return 1

        if dynamodb_table_arn == False:
            logging.info(f"DynamoDB Table {dynamodb_table_name} does not exist")
            return False

        logging.info(f"DynamoDB Table {dynamodb_table_name} already exists")
        logging.debug("Function: _check_existing_dynamodb_table() completed")
        return dynamodb_table_arn

    except AttributeError as e:
        logging.error(f"Attribute Error in check_existing_dynamodb_table: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in check_existing_dynamodb_table: {sys.exc_info()[0]}")
        return 1


def create_dynamodb_table(aws_session=None, dynamodb_client=None, dynamodb_table_name=None, dynamodb_table_region=None, dynamodb_table_read_capacity=5, dynamodb_table_write_capacity=5, dynamodb_table_attributes=[], dynamodb_table_key_schema=[], dynamodb_table_billing_mode="PROVISIONED", aws_account_id=None, dry_run=False):
    """Create a DynamoDB Table based on the passed arguments

    This function creates a DynamoDB Table based on the passed arguments.  Includes a call to check_existing_dynamodb_table to check if the DynamoDB Table already exists.

    Args:
        aws_account_id (str): AWS Account ID
        aws_session (obj): Boto3 session object
        dynamodb_table_name (str): Name of the DynamoDB Table
        dynamodb_table_region (str): Region of the DynamoDB Table
        dynamodb_table_read_capacity (int): Read capacity of the DynamoDB Table
        dynamodb_table_write_capacity (int): Write capacity of the DynamoDB Table
        dynamodb_table_attributes (list): List of attributes for the DynamoDB Table
        dynamodb_table_key_schema (list): List of key schema for the DynamoDB Table
        dynamodb_table_billing_mode (str): Billing mode for the DynamoDB Table
        dry_run (bool): List the DynamoDB Table details only

    Returns:
        dynamodb_table_name (str): Name of the DynamoDB Table

    """
    try:
        logging.debug(f"Function create_dynamodb_table called with arguments: aws_account_id={aws_account_id}, aws_session={aws_session}, dynamodb_table_name={dynamodb_table_name}, dynamodb_table_region={dynamodb_table_region}, dynamodb_table_read_capacity={dynamodb_table_read_capacity}, dynamodb_table_write_capacity={dynamodb_table_write_capacity}, dynamodb_table_attributes={dynamodb_table_attributes}, dynamodb_table_key_schema={dynamodb_table_key_schema}, dynamodb_table_billing_mode={dynamodb_table_billing_mode}, dry_run={dry_run}")

        # Check if both aws_session and dynamodb_client are None and if so exit with an error
        if aws_session == None and dynamodb_client == None:
            logging.error("Error: Both aws_session and dynamodb_client are None")
            return 1

        if dynamodb_client == None:
            dynamodb_client = aws_connect.session_connect(aws_session=aws_session, region=dynamodb_table_region, client_type="dynamodb")

        if dynamodb_client == 1:
            logging.error("Error creating DynamoDB client")
            return 1

        if dynamodb_table_region == None:
            dynamodb_table_region = dynamodb_client.meta.region_name

        output.log_message_section("Planned DynamoDB Table Configuration", top=True, bottom=True)
        logging.info(f"DynamoDB Table Name: {dynamodb_table_name}")
        logging.info(f"DynamoDB Table Region: {dynamodb_table_region}")
        logging.info(f"DynamoDB Table Read Capacity: {dynamodb_table_read_capacity}")
        logging.info(f"DynamoDB Table Write Capacity: {dynamodb_table_write_capacity}")
        logging.info(f"DynamoDB Table Attributes: {dynamodb_table_attributes}")
        logging.info(f"DynamoDB Table Key Schema: {dynamodb_table_key_schema}")
        logging.info(f"DynamoDB Table Billing Mode: {dynamodb_table_billing_mode}")
        logging.info("========================================")

        if aws_account_id == None:
            aws_account_id = aws_connect.get_aws_account_id(aws_session=aws_session)

        # If the dynamodb_table_name does not end with the aws_account_id then append it
        if dynamodb_table_name.endswith(aws_account_id) is False:
            dynamodb_table_name = f"{dynamodb_table_name}-{aws_account_id}"

        # Check if the DynamoDB Table already exists
        # if check_existing_dynamodb_table(dynamodb_client, dynamodb_table_name, ) is True:
        if check_existing_dynamodb_table(aws_session=aws_session, dynamodb_client=dynamodb_client, dynamodb_table_name=dynamodb_table_name, dynamodb_table_region=dynamodb_table_region) is True:
            logging.info(f"DynamoDB Table {dynamodb_table_name} already exists")
            logging.debug("Function: _create_dynamodb_table() completed")
            return dynamodb_table_name

        # If key attributes are not set then return an error
        if dynamodb_table_attributes == []:
            logging.error("DynamoDB Table Attributes not set")
            return 1

        # If key schema is not set then set it to the first attribute
        if dynamodb_table_key_schema == []:
            logging.warning(f"DynamoDB Table Key Schema not set, setting to first attribute: {dynamodb_table_attributes[0]['AttributeName']}")
            dynamodb_table_key_schema = [{'AttributeName': dynamodb_table_attributes[0]['AttributeName'], 'KeyType': 'HASH'}]

        # If list-only/dry-run is set then exit after printing the configuration
        if dry_run is True:
            logging.warning("--list-only/dry-run no DynamoDB Table was created")
            logging.debug("Function: _create_dynamodb_table() completed")
            return dynamodb_table_name

        dynamodb_client.create_table(TableName=dynamodb_table_name, AttributeDefinitions=dynamodb_table_attributes, KeySchema=dynamodb_table_key_schema, ProvisionedThroughput={'ReadCapacityUnits': dynamodb_table_read_capacity, 'WriteCapacityUnits': dynamodb_table_write_capacity}, BillingMode=dynamodb_table_billing_mode)

        logging.debug(f"Exiting Function create_dynamodb_table with dynamodb_table_name: {dynamodb_table_name}")

        return dynamodb_table_name

    except IndexError() as e:
        logging.error(f"Index Error in create_dynamodb_table: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in create_dynamodb_table: {e}")
        return 1
    except ParamValidationError as e:
        logging.error(f"Parameter Validation Error in create_dynamodb_table: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in create_dynamodb_table: {sys.exc_info()[0]}")
        return 1



def print_dynamobd_details (dynamodb_table_name, dynamodb_table_region, aws_session=None, dynamodb_client=None):
    """Print the DynamoDB Table details

    This function prints the DynamoDB Table details based on the passed arguments.

    Args:
        dynamodb_client (obj): Boto3 DynamoDB client object
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        None
    """
    try:
        logging.debug(f"Function print_dynamobd_details called with arguments: dynamodb_client={dynamodb_client}, dynamodb_table_name={dynamodb_table_name}")

        # If dynamodb_table_region or dynamodb_table_name is None then throw an error and return 1
        if dynamodb_table_region is None or dynamodb_table_name is None:
            logging.error("Error in print_dynamobd_details: dynamodb_table_region or dynamodb_table_name is not provided")
            return 1

        # Check if both aws_session and dynamodb_client are None and if so exit with an error
        if aws_session == None and dynamodb_client == None:
            logging.error("Error: Both aws_session and dynamodb_client are None")
            return 1

        if dynamodb_client == None:
            dynamodb_client = aws_connect.session_connect(aws_session=aws_session, region=dynamodb_table_region, client_type="dynamodb")

        if dynamodb_client == 1:
            logging.error("Error creating DynamoDB client")
            return 1

        if dynamodb_table_region == None:
            dynamodb_table_region = dynamodb_client.meta.region_name

        # Get the DynamoDB Table details
        dynamodb_table_details = dynamodb_client.describe_table(TableName=dynamodb_table_name)

        # Print the DynamoDB Table details
        output.log_message_section("DynamoDB Table Details", top=True, bottom=True)
        logging.info(f"DynamoDB Table Name: {dynamodb_table_details['Table']['TableName']}")
        logging.info(f"DynamoDB Table Status: {dynamodb_table_details['Table']['TableStatus']}")
        logging.info(f"DynamoDB Table ARN: {dynamodb_table_details['Table']['TableArn']}")
        logging.info(f"DynamoDB Table Creation Date: {dynamodb_table_details['Table']['CreationDateTime']}")
        logging.info(f"DynamoDB Table Billing Mode: {dynamodb_table_details['Table']['BillingModeSummary']['BillingMode']}")
        logging.info(f"DynamoDB Table Read Capacity: {dynamodb_table_details['Table']['ProvisionedThroughput']['ReadCapacityUnits']}")
        logging.info(f"DynamoDB Table Write Capacity: {dynamodb_table_details['Table']['ProvisionedThroughput']['WriteCapacityUnits']}")
        logging.info(f"DynamoDB Table Item Count: {dynamodb_table_details['Table']['ItemCount']}")
        logging.info(f"DynamoDB Table Size (bytes): {dynamodb_table_details['Table']['TableSizeBytes']}")
        logging.info(f"DynamoDB Table Attribute Definitions: {dynamodb_table_details['Table']['AttributeDefinitions']}")
        logging.info(f"DynamoDB Table Key Schema: {dynamodb_table_details['Table']['KeySchema']}")
        logging.info(f"DynamoDB Table Global Secondary Indexes: {dynamodb_table_details['Table']['GlobalSecondaryIndexes']}")
        logging.info("========================================")

        logging.debug("Exiting Function print_dynamobd_details")

        return

    except KeyError() as e:
        logging.error(f"Key Error in print_dynamodb_details: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in print_dynamodb_details: {e}")
        return 1
    except ParamValidationError as e:
        logging.error(f"Parameter Validation Error in print_dynamodb_details: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in print_dynamodb_details: {sys.exc_info()[0]}")
        return 1


def _check_existing_dynamodb_table_arn(dynamodb_client, dynamodb_table_arn):
    """Check if the DynamoDB Table ARN exists

    This function checks if the DynamoDB Table ARN exists and returns the ARN if it does.

    Args:
        dynamodb_client (obj): Boto3 DynamoDB client object
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        dynamodb_table_arn (str): ARN of the DynamoDB Table
    """
    try:
        logging.debug(f"Function _check_existing_dynamodb_table_arn called with arguments: dynamodb_client={dynamodb_client}, dynamodb_table_name={dynamodb_table_arn}")

        # If dynamodb_table_name is None then throw an error and return 1
        if dynamodb_table_arn is None:
            logging.error("Error in _check_existing_dynamodb_table_arn: dynamodb_table_arn is not provided")
            return 1

        # If dynamodb_client is None then throw an error and return 1
        if dynamodb_client is None:
            logging.error("Error in _check_existing_dynamodb_table_arn: dynamodb_client is not provided")
            return 1

        # Test if the provided ARN already exists
        for table in dynamodb_client.list_tables()['TableNames']:
            if dynamodb_table_arn == dynamodb_client.describe_table(TableName=table)['Table']['TableArn']:
                logging.info(f"DynamoDB Table ARN {dynamodb_table_arn} already exists")
                return dynamodb_table_arn

    except KeyError() as e:
        logging.error(f"Key Error in _check_existing_dynamodb_table_arn: {e}")
        return 1
    except Exception() as e:
        logging.error(f"Unexpected error in _check_existing_dynamodb_table_arn: {e}")
        return 1


def _check_existing_dynamodb_table_name(dynamodb_client, dynamodb_table_name):
    """Check if the DynamoDB Table name exists

    This function checks if the DynamoDB Table name exists and returns the name if it does.

    Args:
        dynamodb_client (obj): Boto3 DynamoDB client object
        dynamodb_table_name (str): Name of the DynamoDB Table

    Returns:
        dynamodb_table_name (str): Name of the DynamoDB Table
    """
    try:
        logging.debug(f"Function _check_existing_dynamodb_table_name called with arguments: dynamodb_client={dynamodb_client}, dynamodb_table_name={dynamodb_table_name}")

        # If dynamodb_table_name is None then throw an error and return 1
        if dynamodb_table_name is None:
            logging.error("Error in _check_existing_dynamodb_table_name: dynamodb_table_name is not provided")
            return 1

        # If dynamodb_client is None then throw an error and return 1
        if dynamodb_client is None:
            logging.error("Error in _check_existing_dynamodb_table_name: dynamodb_client is not provided")
            return 1

        # Test if the provided table name already exists
        table_arn = None
        for table in dynamodb_client.list_tables()['TableNames']:
            if dynamodb_table_name == table:
                logging.info(f"DynamoDB Table {dynamodb_table_name} already exists")
                # Get the DynamoDB Table ARN
                table_arn = dynamodb_client.describe_table(TableName=table)['Table']['TableArn']
                return table_arn

    except KeyError() as e:
        logging.error(f"Key Error in _check_existing_dynamodb_table_name: {e}")
        return 1
    except Exception() as e:
        logging.error(f"Unexpected error in _check_existing_dynamodb_table_name: {e}")
        return 1