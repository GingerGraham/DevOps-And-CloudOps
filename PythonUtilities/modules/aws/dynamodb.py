#!/usr/bin/env python3

"""DynamoDB utilities

This module contains functions to interact with DynamoDB.

Functions:

    check_existing_dynamodb_table(aws_session, dynamodb_table_name, dynamodb_table_region)
    create_dynamodb_table(aws_account_id, aws_session, dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity=5, dynamodb_table_write_capacity=5, dynamodb_table_attributes=[], dynamodb_table_key_schema=[], dynamodb_table_billing_mode="PROVISIONED", list_only=False)

"""


# Import global modules
import logging
import sys

# Import local modules
import modules.output as output

# Import third-party modules
from botocore.exceptions import ClientError


def check_existing_dynamodb_table(aws_session=None, dynamodb_client=None, dynamodb_table_name=None, dynamodb_table_region=None):
    """Check if a DynamoDB Table already exists

    This function checks if a DynamoDB Table already exists.

    Args:
        aws_session (obj): Boto3 session object - not required if dynamodb_client is provided instead
        dynamodb_client (obj): Boto3 DynamoDB client object - not required if aws_session is provided instead
        dynamodb_table_name (str): Name of the DynamoDB Table
        dynamodb_table_region (str): Region of the DynamoDB Table

    Returns:
        table_exists (bool): True if the DynamoDB Table exists, False if it does not exist
    """
    try:
        logging.debug(f"Function check_existing_dynamodb_table called with arguments: aws_session={aws_session}, dynamodb_table_name={dynamodb_table_name}, dynamodb_table_region={dynamodb_table_region}")

        logging.info(f"Checking if DynamoDB Table {dynamodb_table_name} already exists")

        # Check if both aws_session and dynamodb_client are None and if so exit with an error
        if aws_session == None and dynamodb_client == None:
            logging.error("Error: Both aws_session and dynamodb_client are None")
            return 1

        # Check if we were passed a DynamoDB client or if we need to create one
        if dynamodb_client == None:
            # Create a DynamoDB client using provided AWS Account credentials and the _create_dynamodb_client function
            dynamodb_client = _create_dynamodb_client(aws_session, dynamodb_table_region)
            # Check to make sure that the DynamoDB client was created successfully and does not equal 1 (error)
            if dynamodb_client == 1:
                logging.error("Error creating DynamoDB client")
                return 1

        # If the dynamodb_table_region is None then set it to the region of the dynamodb_client
        if dynamodb_table_region == None:
            dynamodb_table_region = dynamodb_client.meta.region_name

        # Check if table name or region are None and if so exit with an error
        if dynamodb_table_name == None or dynamodb_table_region == None:
            logging.error("Error: DynamoDB table name or region is None")
            return 1

        # Check if the DynamoDB Table already exists
        table_exists = False
        for table in dynamodb_client.list_tables()['TableNames']:
            if table == dynamodb_table_name:
                logging.debug(f"DynamoDB Table {dynamodb_table_name} already exists")
                table_exists = True
                break

        logging.debug("Function: _check_existing_dynamodb_table() completed")

        return table_exists

    except AttributeError as e:
        logging.error(f"Attribute Error in check_existing_dynamodb_table: {e}")
        return 1
    except ClientError as e:
        logging.error(f"Client Error in check_existing_dynamodb_table: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in check_existing_dynamodb_table: {sys.exc_info()[0]}")
        return 1


def create_dynamodb_table(aws_session, dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity=5, dynamodb_table_write_capacity=5, dynamodb_table_attributes=[], dynamodb_table_key_schema=[], dynamodb_table_billing_mode="PROVISIONED", aws_account_id=None, list_only=False):
    """Create a DynamoDB Table based on the passed arguments

    This function creates a DynamoDB Table based on the passed arguments.

    Args:
        aws_account_id (str): AWS Account ID
        aws_session (obj): Boto3 session object
        dynamodb_table_name (str): Name of the DynamoDB Table
        dynamodb_table_region (str): Region of the DynamoDB Table
        dynamodb_table_read_capacity (int): Read capacity of the DynamoDB Table
        dynamodb_table_write_capacity (int): Write capacity of the DynamoDB Table
        dynamodb_table_attributes (list): List of attributes for the DynamoDB Table
        dynamodb_table_key_schema (list): List of key schema for the DynamoDB Table
        list_only (bool): List the DynamoDB Table details only

    Returns:
        dynamodb_table_name (str): Name of the DynamoDB Table

    """
    try:
        logging.debug(f"Function create_dynamodb_table called with arguments: aws_account_id={aws_account_id}, aws_session={aws_session}, dynamodb_table_name={dynamodb_table_name}, dynamodb_table_region={dynamodb_table_region}, dynamodb_table_read_capacity={dynamodb_table_read_capacity}, dynamodb_table_write_capacity={dynamodb_table_write_capacity}, dynamodb_table_attributes={dynamodb_table_attributes}, dynamodb_table_key_schema={dynamodb_table_key_schema}, dynamodb_table_billing_mode={dynamodb_table_billing_mode}, list_only={list_only}")

        # If the DynamoDB Table region is not passed then use the region of the AWS Account
        if dynamodb_table_region is None:
            dynamodb_table_region = aws_session.region_name

        output.log_message_section("DynamoDB Table Configuration", top=True, bottom=True)
        logging.info(f"DynamoDB Table Name: {dynamodb_table_name}")
        logging.info(f"DynamoDB Table Region: {dynamodb_table_region}")
        logging.info(f"DynamoDB Table Read Capacity: {dynamodb_table_read_capacity}")
        logging.info(f"DynamoDB Table Write Capacity: {dynamodb_table_write_capacity}")
        logging.info(f"DynamoDB Table Attributes: {dynamodb_table_attributes}")
        logging.info(f"DynamoDB Table Key Schema: {dynamodb_table_key_schema}")
        logging.info(f"DynamoDB Table Billing Mode: {dynamodb_table_billing_mode}")
        logging.info("========================================")

        # Create a DynamoDB client using provided AWS Account credentials and the _create_dynamodb_client function
        dynamodb_client = _create_dynamodb_client(aws_session, dynamodb_table_region)
        # Check to make sure that the DynamoDB client was created successfully and does not equal 1 (error)
        if dynamodb_client == 1:
            logging.error("Error creating DynamoDB client")
            return 1

        # If aws_account_id is not None then append it to the DynamoDB Table name
        dynamodb_table_name = f"{dynamodb_table_name}-{aws_account_id}"

        # Check if the DynamoDB Table already exists
        # if check_existing_dynamodb_table(dynamodb_client, dynamodb_table_name, ) is True:
        if check_existing_dynamodb_table(aws_session, dynamodb_table_name, dynamodb_table_region) is True:
            logging.info(f"DynamoDB Table {dynamodb_table_name} already exists")
            logging.debug("Function: _create_dynamodb_table() completed")
            return dynamodb_table_name

        # If list-only/dry-run is set then exit after printing the configuration
        if list_only is True:
            logging.warning("--list-only/dry-run no DynamoDB Table was created")
            logging.debug("Function: _create_dynamodb_table() completed")
            return dynamodb_table_name

        # If list-only/dry-run is not set then create the DynamoDB Table
        # based on passed dynamodb_table_name, dynamodb_table_region, dynamodb_table_read_capacity, dynamodb_table_write_capacity arguments create a DynamoDB Table with a primary key of LockID
        dynamodb_client.create_table(TableName=dynamodb_table_name, AttributeDefinitions=dynamodb_table_attributes, KeySchema=dynamodb_table_key_schema, ProvisionedThroughput={'ReadCapacityUnits': dynamodb_table_read_capacity, 'WriteCapacityUnits': dynamodb_table_write_capacity}, BillingMode=dynamodb_table_billing_mode)

        logging.debug(f"Exiting Function create_dynamodb_table with dynamodb_table_name: {dynamodb_table_name}")

        return dynamodb_table_name

    except ClientError as e:
        logging.error(f"Client Error in create_dynamodb_table: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in create_dynamodb_table: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in create_dynamodb_table: {sys.exc_info()[0]}")
        return 1


def _create_dynamodb_client(aws_session, dynamodb_table_region):
    """Create a DynamoDB client

    This internal function creates a DynamoDB client based on the passed arguments.

    Args:
        aws_session (obj): Boto3 session object
        dynamodb_table_region (str): Region of the DynamoDB Table

    Returns:
        dynamodb_client (obj): Boto3 DynamoDB client object
    """
    try:
        logging.debug(f"Function _create_dynamodb_client called with arguments: aws_session={aws_session}, dynamodb_table_region={dynamodb_table_region}")

        # Create a DynamoDB client based on the passed dynamodb_table_region
        logging.debug("Creating a DynamoDB client")
        dynamodb_client = aws_session.client('dynamodb', region_name = dynamodb_table_region)
        logging.debug(f"DynamoDB client created successfully: {dynamodb_client}")

        logging.debug(f"Exiting Function _create_dynamodb_client with dynamodb_client: {dynamodb_client}")

        return dynamodb_client

    except ClientError as e:
        logging.error(f"Error in _create_dynamodb_client: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Error in _create_dynamodb_client: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in _create_dynamodb_client: {sys.exc_info()[0]}")
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

        # Test if aws_session is None and dynamodb_client is None and if so throw an error and return 1
        if aws_session is None and dynamodb_client is None:
            logging.error("Error in print_dynamobd_details: aws_session and dynamodb_client are both None")
            return 1

        # If dynamodb_client is None then create a DynamoDB client using provided AWS Account credentials and the _create_dynamodb_client function
        if dynamodb_client is None:
            dynamodb_client = _create_dynamodb_client(aws_session, dynamodb_table_region)

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

    except ClientError as e:
        logging.error(f"Client Error in print_dynamodb_details: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in print_dynamodb_details: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in print_dynamodb_details: {sys.exc_info()[0]}")
        return 1
