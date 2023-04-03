#!/usr/bin/env python3

"""KMS utilities
"""

# Import global modules
import logging

# Import local modules
import modules.output as output

# Import third party modules - see requirements.txt
from botocore.exceptions import ClientError, ParamValidationError

# To do
# - Add a function to check if a KMS Key ID already exists - determine what we should return if it does exist
# - Add a function to create a KMS Key ID
# - Add an internal function to create a boto3 kms client session
# - Add a function to print the details of a KMS Key ID to logging.info

def check_existing_kms_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_id=None):
    """Check Existing KMS Key

    This function checks if a KMS Key exists either by KMS Key Alias or KMS Key ID; where both are provided the KMS Key ID is used.

    """
    try:
        logging.debug(f"Function: check_existing_kms_key() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}")

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if kms_key_alias == None and kms_key_id == None:
            logging.error("No KMS Key Alias or KMS Key ID provided")
            return 1

        if kms_client == None and kms_key_region == None:
            kms_key_region = aws_session.region_name
            logging.info(f"KMS Key Region not provided, using region from AWS Session: {kms_key_region}")

        if kms_client == None:
            kms_client = _create_kms_client(aws_session=aws_session, kms_key_region=kms_key_region)

        logging.info(f"Checking if KMS Key ID {kms_key_id} or KMS Key Alias {kms_key_alias} already exists")

        # Using _check_existing_kms_key_id() to check if a KMS Key ID already exists
        if kms_key_id != None:
            key_arn = _check_existing_kms_key_id(kms_client=kms_client, kms_key_id=kms_key_id)

        if kms_key_alias != None:
            key_arn = _check_existing_kms_key_alias(kms_client=kms_client, kms_key_alias=kms_key_alias)

        if key_arn == False:
            logging.info(f"KMS Key {kms_key_alias} does not exist")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return False

        if key_arn == 1:
            logging.error(f"Error checking KMS Key {kms_key_alias}")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return 1

        logging.info(f"KMS Key {kms_key_alias} already exists")
        logging.debug(f"Function: check_existing_kms_key() completed")
        return key_arn

    except:
        logging.error(f"Unexpected error in check_existing_kms_key()")
        return 1


def create_symmetric_encrypt_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_spec='SYMMETRIC_DEFAULT', dry_run=False):
    """Create KMS Key

    This function creates a KMS Key.

    """
    try:
        logging.debug(f"Function: create_symmetric_encrypt_key() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}, kms_key_spec = {kms_key_spec}, dry_run = {dry_run}")

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if aws_session == None and kms_key_region == None:
            kms_key_region = aws_session.region_name
            logging.info(f"KMS Key Region not provided, using region from AWS Session: {kms_key_region}")

        if kms_client == None:
            kms_client = _create_kms_client(aws_session=aws_session, kms_key_region=kms_key_region)

        logging.info(f"Creating KMS Key in region {kms_key_region} with spec {kms_key_spec}")

        # Check if the KMS Key already exists using check_existing_kms_key()
        key_arn = check_existing_kms_key(aws_session=aws_session, kms_client=kms_client, kms_key_region=kms_key_region, kms_key_alias=kms_key_alias)

        if key_arn == 1:
            logging.error(f"Error creating KMS Key {kms_key_alias}")
            logging.debug(f"Function: create_symmetric_encrypt_key() completed")
            return 1

        if key_arn != False:
            logging.info(f"KMS Key {kms_key_alias} already exists")
            logging.debug(f"Function: create_symmetric_encrypt_key() completed")
            return key_arn

        # Create the KMS Key
        # To do - create key or report if list only
        if dry_run == True:
            logging.info(f"Dry run only - Would create single region symmetric KMS Key {kms_key_alias} for ENCRYPT_DECRYPT with spec {kms_key_spec}")
            logging.debug(f"Function: create_symmetric_encrypt_key() completed")
            return 0

        kms_key = kms_client.create_key(
            Description=f"Symmetric KMS Key for ENCRYPT_DECRYPT with spec {kms_key_spec}",
            KeyUsage='ENCRYPT_DECRYPT',
            KeySpec=kms_key_spec,
            MultiRegion=False
        )

        key_arn = kms_key['KeyMetadata']['Arn']

        # Add Alias to KMS Key
        alias_success = add_kms_key_alias(aws_session=aws_session, kms_client=kms_client, kms_key_region=kms_key_region, kms_key_alias=kms_key_alias, kms_key_arn=key_arn, dry_run=dry_run)

        if alias_success == 1:
            logging.error(f"Error creating KMS Key {kms_key_alias}")
            logging.debug(f"Function: create_symmetric_encrypt_key() completed")
            return 1

        logging.debug(f"Function: create_symmetric_encrypt_key() completed")
        return key_arn

    except:
        logging.error(f"Unexpected error in check_existing_kms_key()")
        return 1


def add_kms_key_alias(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_arn=None, dry_run=False):
    """Add Alias to KMS Key
    """
    try:
        logging.debug(f"Function: add_kms_key_alias() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}, kms_key_arn = {kms_key_arn}, dry_run = {dry_run}")

        logging.info(f"Adding Alias {kms_key_alias} to KMS Key {kms_key_arn}")

        if kms_key_alias == None:
            logging.error("No KMS Key Alias provided")
            return 1

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if aws_session == None and kms_key_region == None:
            kms_key_region = aws_session.region_name
            logging.info(f"KMS Key Region not provided, using region from AWS Session: {kms_key_region}")

        if kms_client == None:
            kms_client = _create_kms_client(aws_session=aws_session, kms_key_region=kms_key_region)

        if dry_run == True:
            logging.info(f"Dry run only - Would add alias {kms_key_alias} to KMS Key {kms_key_arn}")
            logging.debug(f"Function: add_kms_key_alias() completed")
            return 0

        # If KMS Key Alias does not have alias/ prefix, add it
        if kms_key_alias.startswith("alias/") == False:
            kms_key_alias = "alias/" + kms_key_alias

        kms_client.create_alias(
            AliasName=kms_key_alias,
            TargetKeyId=kms_key_arn
        )

        logging.debug(f"Function: add_kms_key_alias() completed")
        return 0

    except ClientError as e:
        logging.error(f"Client error in add_kms_key_alias(): {e}")
        return 1
    except ParamValidationError as e:
        logging.error(f"Parameter validation error in add_kms_key_alias(): {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error in add_kms_key_alias(): {e}")
        return 1


def _check_existing_kms_key_id(kms_client=None, kms_key_id=None):
    """ Check Existing KMS Key ID

    This function checks if a KMS Key ID already exists; if it does it returns the KMS Key ARN.

    Args:
        kms_client (boto3.client): A boto3 KMS client session
        kms_key_id (str): A KMS Key ID

    Returns:
        str: The KMS Key ARN

    """
    try:
        logging.debug(f"Function: _check_existing_kms_key_id() started with args: kms_client = {kms_client}, kms_key_id = {kms_key_id}")

        logging.info(f"Checking if KMS Key ID {kms_key_id} already exists")

        if kms_client == None:
            logging.error("No KMS Client provided")
            return 1

        if kms_key_id == None:
            logging.error("No KMS Key ID provided")
            return 1

        keys_list = kms_client.list_keys()
        for key in keys_list['Keys']:
            key_id = key['KeyId']
            key_arn = kms_client.describe_key(KeyId=key_id)['KeyMetadata']['Arn']
            if key_id == kms_key_id:
                logging.info(f"KMS Key ID {kms_key_id} already exists")
                logging.debug(f"Function: _check_existing_kms_key_id() completed")
                return key_arn

        logging.info(f"KMS Key ID {kms_key_id} does not exist")
        logging.debug(f"Function: _check_existing_kms_key_id() completed")
        return False

    except:
        logging.error(f"Unexpected error in _check_existing_kms_key_id()")
        return 1


def _check_existing_kms_key_alias(kms_client=None, kms_key_alias=None):
    """Check Existing KMS Key Alias

    This function checks if a KMS Key Alias already exists; if it does it returns the KMS Key ARN.

    Args:
        kms_client (boto3.client): A boto3 KMS client session
        kms_key_alias (str): A KMS Key Alias

    Returns:
        str: The KMS Key ARN

    """
    try:
        logging.debug(f"Function: _check_existing_kms_key_alias() started with args: kms_client = {kms_client}, kms_key_alias = {kms_key_alias}")

        logging.info(f"Checking if KMS Key Alias {kms_key_alias} already exists")

        if kms_client == None:
            logging.error("No KMS Client provided")
            return 1

        if kms_key_alias == None:
            logging.error("No KMS Key Alias provided")
            return 1

        # Check if the KMS Key Alias already exists
        keys_list = kms_client.list_keys()
        for key in keys_list['Keys']:
            key_id = key['KeyId']
            key_arn = kms_client.describe_key(KeyId=key_id)['KeyMetadata']['Arn']
            key_aliases = kms_client.list_aliases(KeyId=key_id)
            for key_alias in key_aliases['Aliases']:
                if key_alias['AliasName'] == kms_key_alias:
                    logging.info(f"KMS Key ID {key_id} already exists")
                    logging.debug(f"Function: _check_existing_kms_key_alias() completed")
                    return key_arn

        logging.info(f"KMS Key Alias {kms_key_alias} does not exist")
        logging.debug(f"Function: _check_existing_kms_key_alias() completed")
        return False

    except Exception as e:
        logging.error(f"Unexpected error in _check_existing_kms_key_alias(): {e}")
        return 1


def _create_kms_client(aws_session=None, kms_key_region=None):
    """Create KMS Client
    """
    try:
        logging.debug(f"Function: _create_kms_client() started with args: aws_session = {aws_session}, kms_key_region = {kms_key_region}")

        logging.info(f"Creating KMS Client")

        if aws_session == None:
            logging.error("No AWS Session provided")
            return False

        if kms_key_region == None:
            kms_client = aws_session.client('kms')

        if kms_key_region != None:
            kms_client = aws_session.client('kms', region_name=kms_key_region)

        logging.debug(f"KMS Client created: {kms_client}")

        logging.debug(f"Function: _create_kms_client() completed")

        return kms_client

    except ClientError as e:
        logging.error(f"Client Error in _create_kms_client(): {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in _create_kms_client(): {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error in _create_kms_client(): {e}")
        return 1

        # Create a KMS Client session


# Notes
# Code below this line is example code from a previous script and needs to be split out into functions for this module

# Create a KMS Client session
        kms_client = aws_session.client('kms')

        # Open variables for kms_key_id and kms_key_arn
        kms_key_id = None
        kms_key_arn = None

        # Set a variable to check if the KMS Key already exists
        key_exists = False

        # Prepare an alias for the KMS Key
        kms_key_alias = 'alias/{0}'.format(args.bucket_name)

        # Check if the KMS Key ID already exists
        if args.bucket_kms_key_id is None and args.bucket_encryption is True:
            # Check if the KMS Key Alias already exists
            keys_list = kms_client.list_keys()
            for key in keys_list['Keys']:
                key_id = key['KeyId']
                key_arn = kms_client.describe_key(KeyId=key_id)['KeyMetadata']['Arn']
                key_aliases = kms_client.list_aliases(KeyId=key_id)
                for key_alias in key_aliases['Aliases']:
                    if key_alias['AliasName'] == kms_key_alias:
                        kms_key_id = key_id
                        kms_key_arn = key_arn
                        key_exists = True
                        logging.info("KMS Key ID {0} already exists".format(kms_key_id))
                        # Update the bucket_config with the KMS Key ID and enable the use of bucket key to reduce KMS calls
                        bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': kms_key_arn}, 'BucketKeyEnabled': True}]}
                        break
                if key_exists is True: # Break out of the for loop if the key exists
                    break

        # Where a KMS key ID was passed and encryption is enabled then find the ARN and use the passed KMS key
        if args.bucket_kms_key_id is not None and args.bucket_encryption is True:
            kms_key_id = args.bucket_kms_key_id
            kms_key_arn = kms_client.describe_key(KeyId=args.bucket_kms_key_id)['KeyMetadata']['Arn']
            kms_key_alias = kms_client.list_aliases(KeyId=args.bucket_kms_key_id)['Aliases'][0]['AliasName']
            key_exists = True
            bucket_config['ServerSideEncryptionConfiguration'] = {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms', 'KMSMasterKeyID': kms_key_arn}, 'BucketKeyEnabled': True}]}

        # If list_only is True log what what we would do if the key does not already exist
        if key_exists is not True and args.bucket_encryption is True and args.list_only is True:
            logging.info("KMS Key ID {0} does not exist, would create KMS Key ID {0}".format(kms_key_alias))

        # Create key
        if key_exists is not True and args.bucket_encryption is True and args.list_only is False:
            create_key = True
        else:
            create_key = False