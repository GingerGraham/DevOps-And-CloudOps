#!/usr/bin/env python3

"""KMS utilities

This module contains functions to manage AWS KMS Keys.

Author: Graham Watts
Date: 2023-04-09
Version: 1.0.2

Classes:
    N/A

Public Functions:
    check_existing_kms_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_id=None): Check if a KMS Key exists either by KMS Key Alias or KMS Key ID; where both are provided the KMS Key ID is used.

    create_singleregion_encrypt_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_spec='SYMMETRIC_DEFAULT', dry_run=False): Create a KMS Key in a single region with the specified KMS Key Alias and KMS Key Spec.

    add_kms_key_alias(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_id=None, dry_run=False): Add a KMS Key Alias to a KMS Key.

    print_kms_key_details(kms_key_arn=None, kms_key_id=None, kms_key_alias=None, kms_key_region=None, kms_client=None): Print the details of a KMS Key to logging.info.

Internal Functions:
    _check_existing_kms_key_id(kms_client=None, kms_key_id=None): Check if a KMS Key ID exists.

    _check_existing_kms_key_alias(kms_client=None, kms_key_alias=None): Check if a KMS Key Alias exists.

    _check_existing_kms_key_arn(kms_client=None, kms_key_arn=None): Check if a KMS Key ARN exists.

    _print_kms_key_alias(kms_client=None, kms_key_alias=None): Print the details of a KMS Key Alias to logging.info.

    _print_kms_key_rotation_policy(kms_client=None, kms_key_id=None): Print the details of a KMS Key Rotation Policy to logging.info.

"""

# Import global modules
import logging

# Import local modules
import modules.output as output
import modules.aws.connect as aws_connect

# Import third party modules - see requirements.txt
from botocore.exceptions import ClientError, ParamValidationError

# To do
# - Add a function to print the details of a KMS Key ID to logging.info

def check_existing_kms_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_id=None, kms_key_arn=None):
    """Check Existing KMS Key

    This function checks if a KMS Key exists either by KMS Key Alias, KMS Key ID or KMS Key ARN; where two or more are provided the precedence is KMS Key ARN, KMS Key ID, KMS Key Alias.

    Args:
        aws_session (boto3.session.Session): AWS Session
        kms_client (boto3.client('kms')): KMS Client
        kms_key_region (str): KMS Key Region
        kms_key_alias (str): KMS Key Alias
        kms_key_id (str): KMS Key ID
        kms_key_arn (str): KMS Key ARN

    Returns:
        key_arn (str): KMS Key ARN
        False: KMS Key does not exist
        1: Error checking KMS Key

    Example:
        >>> check_existing_kms_key(aws_session=aws_session, kms_key_region='eu-west-1', kms_key_alias='alias/MyKMSKey')
        'arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012'

    """
    try:
        logging.debug(f"Function: check_existing_kms_key() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}, kms_key_id = {kms_key_id}, kms_key_arn = {kms_key_arn}")

        if kms_key_alias == None and kms_key_id == None and kms_key_arn == None:
            logging.error("No KMS Key Alias, KMS Key ID or KMS Key ARN provided")
            return 1

        if kms_key_alias != None and kms_key_alias.startswith('alias/') == False:
            kms_key_alias = 'alias/' + kms_key_alias

        if kms_key_arn != None and kms_key_arn.startswith('arn:aws:kms:') == False:
            logging.error(f"KMS Key ARN {kms_key_arn} is not valid")
            return 1

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if kms_client == None:
            kms_client = aws_connect.session_connect(aws_session=aws_session, region=kms_key_region, client_type='kms')

        if kms_client == 1:
            logging.error(f"Error creating KMS Client")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return 1

        # Setting a default value for key_arn variable to False
        key_arn = False

        if kms_key_arn != None:
            logging.debug(f"Checking KMS Key ARN {kms_key_arn}")
            key_arn = _check_existing_kms_key_arn(kms_client=kms_client, kms_key_arn=kms_key_arn)

        if kms_key_id != None and (key_arn == False or key_arn == 1 or key_arn == None):
            logging.debug(f"Checking KMS Key ID {kms_key_id}")
            key_arn = _check_existing_kms_key_id(kms_client=kms_client, kms_key_id=kms_key_id)

        if kms_key_alias != None and (key_arn == False or key_arn == 1 or key_arn == None):
            logging.debug(f"Checking KMS Key Alias {kms_key_alias}")
            key_arn = _check_existing_kms_key_alias(kms_client=kms_client, kms_key_alias=kms_key_alias)

        if key_arn == False:
            logging.info(f"No KMS Key found")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return False

        if key_arn == 1:
            logging.error(f"Error checking KMS Key")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return 1

        logging.info(f"KMS Key already exists: {key_arn}")
        logging.debug(f"Function: check_existing_kms_key() completed")
        return key_arn

    except:
        logging.error(f"Unexpected error in check_existing_kms_key()")
        return 1


def create_singleregion_encrypt_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_spec='SYMMETRIC_DEFAULT', dry_run=False):
    """Create KMS Key

    This function creates a KMS Key in a single region with the specified KMS Key Alias and KMS Key Spec.

    Args:
        aws_session (boto3.session.Session): AWS Session
        kms_client (boto3.client('kms')): KMS Client
        kms_key_region (str): KMS Key Region
        kms_key_alias (str): KMS Key Alias
        kms_key_spec (str): KMS Key Spec - Default: SYMMETRIC_DEFAULT
        dry_run (bool): Dry Run - Default: False

    Returns:
        key_arn (str): KMS Key ARN
        0: Dry run successful
        1: Error creating KMS Key

    Example:
        >>> create_singleregion_encrypt_key(aws_session=aws_session, kms_key_region='eu-west-1', kms_key_alias='alias/MyKMSKey', kms_key_spec='SYMMETRIC_DEFAULT')
        'arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012'

        >>> create_singleregion_encrypt_key(aws_session=aws_session, kms_key_region='eu-west-1', kms_key_alias='alias/MyKMSKey', kms_key_spec='SYMMETRIC_DEFAULT', dry_run=True)
        0

    """
    try:
        logging.debug(f"Function: create_singleregion_encrypt_key() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}, kms_key_spec = {kms_key_spec}, dry_run = {dry_run}")

        if kms_key_alias == None and kms_key_id == None:
            logging.error("No KMS Key Alias or KMS Key ID provided")
            return 1

        if kms_key_alias != None and kms_key_alias.startswith('alias/') == False:
            kms_key_alias = 'alias/' + kms_key_alias

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if kms_client == None:
            kms_client = aws_connect.session_connect(aws_session=aws_session, region=kms_key_region, client_type='kms')

        if kms_client == 1:
            logging.error(f"Error creating KMS Client")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return 1

        if kms_key_region == None:
            kms_key_region = kms_client.meta.region_name

        logging.info(f"Creating KMS Key in region {kms_key_region} with spec {kms_key_spec}")

        # Check if the KMS Key already exists using check_existing_kms_key()
        key_arn = check_existing_kms_key(aws_session=aws_session, kms_client=kms_client, kms_key_region=kms_key_region, kms_key_alias=kms_key_alias)

        if key_arn == 1:
            logging.error(f"Error creating KMS Key {kms_key_alias}")
            logging.debug(f"Function: create_singleregion_encrypt_key() completed")
            return 1

        if key_arn != False:
            logging.info(f"KMS Key {kms_key_alias} already exists")
            logging.debug(f"Function: create_singleregion_encrypt_key() completed")
            return key_arn

        # Create the KMS Key
        # To do - create key or report if list only
        if dry_run == True:
            logging.info(f"Dry run only - Would create single region symmetric KMS Key {kms_key_alias} for ENCRYPT_DECRYPT with spec {kms_key_spec}")
            logging.debug(f"Function: create_singleregion_encrypt_key() completed")
            return 0

        kms_key = kms_client.create_key(
            Description=f"Single region symmetric KMS Key for ENCRYPT_DECRYPT created by python script {__file__}",
            KeyUsage='ENCRYPT_DECRYPT',
            KeySpec=kms_key_spec,
            MultiRegion=False
        )

        key_arn = kms_key['KeyMetadata']['Arn']

        # Add Alias to KMS Key if provided
        if kms_key_alias != None:
            alias_success = add_kms_key_alias(aws_session=aws_session, kms_client=kms_client, kms_key_region=kms_key_region, kms_key_alias=kms_key_alias, kms_key_arn=key_arn, dry_run=dry_run)

        if alias_success == 1:
            logging.error(f"Error creating KMS Key {kms_key_alias}")
            logging.debug(f"Function: create_singleregion_encrypt_key() completed")
            return 1

        logging.debug(f"Function: create_singleregion_encrypt_key() completed")
        return key_arn

    except:
        logging.error(f"Unexpected error in check_existing_kms_key()")
        return 1


def add_kms_key_alias(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None, kms_key_arn=None, dry_run=False):
    """Add Alias to KMS Key

    This function adds an Alias to a KMS Key.

    Args:
        aws_session (boto3.session.Session): AWS Session
        kms_client (boto3.client('kms')): KMS Client
        kms_key_region (str): KMS Key Region
        kms_key_alias (str): KMS Key Alias
        kms_key_arn (str): KMS Key ARN
        dry_run (bool): Dry Run

    Returns:
        0: Successful
        1: Error adding KMS Key Alias

    Example:
        >>> add_kms_key_alias(aws_session=aws_session, kms_key_region='eu-west-1', kms_key_alias='alias/MyKMSKey', kms_key_arn='arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012')
        0

        >>> add_kms_key_alias(aws_session=aws_session, kms_key_region='eu-west-1', kms_key_alias='alias/MyKMSKey', kms_key_arn='arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012', dry_run=True)
        0

    """
    try:
        logging.debug(f"Function: add_kms_key_alias() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_alias = {kms_key_alias}, kms_key_arn = {kms_key_arn}, dry_run = {dry_run}")

        if kms_key_alias == None:
            logging.error("No KMS Key Alias provided")
            return 1

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        if kms_key_alias != None and kms_key_alias.startswith('alias/') == False:
            kms_key_alias = 'alias/' + kms_key_alias

        if kms_key_arn != None and kms_key_arn.startswith('arn:aws:kms:') == False:
            logging.error("KMS Key ARN does not start with arn:aws:kms:")
            return 1

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if kms_client == None:
            kms_client = aws_connect.session_connect(aws_session=aws_session, region=kms_key_region, client_type='kms')

        if kms_client == 1:
            logging.error(f"Error creating KMS Client")
            logging.debug(f"Function: check_existing_kms_key() completed")
            return 1

        logging.info(f"Adding Alias {kms_key_alias} to KMS Key {kms_key_arn}")

        # Check if the KMS Key Alias already exists using _check_existing_kms_key_alias()
        alias_exists = _check_existing_kms_key_alias(kms_client=kms_client, kms_key_alias=kms_key_alias)

        if alias_exists == 1:
            logging.error(f"Error checking for KMS Key Alias {kms_key_alias}")
            logging.debug(f"Function: add_kms_key_alias() completed")
            return 1

        if alias_exists != False:
            logging.info(f"KMS Key Alias {kms_key_alias} already exists")
            logging.debug(f"Function: add_kms_key_alias() completed")
            return 0

        if alias_exists == False and dry_run == True:
            logging.info(f"Dry run only - Would add alias {kms_key_alias} to KMS Key {kms_key_arn}")
            logging.debug(f"Function: add_kms_key_alias() completed")
            return 0

        logging.info(f"Adding alias {kms_key_alias} to KMS Key {kms_key_arn}")
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


def print_kms_key_details(aws_session=None, kms_client=None, kms_key_region=None, kms_key_id=None, kms_key_alias=None, kms_key_arn=None):
    """ Print KMS Key Details

    This function prints the details of a KMS Key based on the KMS Key ID, KMS Key Alias or KMS Key ARN.

    Args:
        aws_session (boto3.session.Session): AWS Session
        kms_client (boto3.client('kms')): KMS Client
        kms_key_region (str): KMS Key Region
        kms_key_id (str): KMS Key ID
        kms_key_alias (str): KMS Key Alias
        kms_key_arn (str): KMS Key ARN

    Returns:
        0: Successful
        1: Error printing KMS Key details

    """
    try:
        logging.debug(f"Function: print_kms_key_details() started with args: aws_session = {aws_session}, kms_client = {kms_client}, kms_key_region = {kms_key_region}, kms_key_id = {kms_key_id}, kms_key_alias = {kms_key_alias}, kms_key_arn = {kms_key_arn}")

        if aws_session == None and kms_client == None:
            logging.error("No AWS Session or KMS Client provided")
            return 1

        if kms_client == None:
            kms_client = aws_connect.session_connect(aws_session=aws_session, region=kms_key_region, client_type='kms')

        if kms_key_arn == None and kms_key_id != None:
            kms_key_arn = _check_existing_kms_key_id(kms_client=kms_client, kms_key_id=kms_key_id)

        if kms_key_arn == None and kms_key_alias != None:
            kms_key_arn = _check_existing_kms_key_alias(kms_client=kms_client, kms_key_alias=kms_key_alias)

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        if kms_key_arn.startswith("arn:aws:kms:") == False:
            logging.error("KMS Key ARN is not valid")
            return 1

        kms_key_details = kms_client.describe_key(KeyId=kms_key_arn)

        output.log_message_section("KMS Key Details", top=True, bottom=True)
        logging.info(f"KMS Key ID: {kms_key_details['KeyMetadata']['KeyId']}")
        logging.info(f"KMS Key ARN: {kms_key_details['KeyMetadata']['Arn']}")
        logging.info(f"KMS Key Description: {kms_key_details['KeyMetadata']['Description']}")
        logging.info(f"KMS Key Enabled: {kms_key_details['KeyMetadata']['Enabled']}")
        logging.info(f"KMS Key Key Usage: {kms_key_details['KeyMetadata']['KeyUsage']}")
        logging.info(f"KMS Key Key State: {kms_key_details['KeyMetadata']['KeyState']}")
        logging.info(f"KMS Key Customer Master Key Spec: {kms_key_details['KeyMetadata']['CustomerMasterKeySpec']}")
        logging.info(f"KMS Key Spec: {kms_key_details['KeyMetadata']['KeySpec']}")
        logging.info(f"KMS Key Creation Date: {kms_key_details['KeyMetadata']['CreationDate']}")
        if kms_key_details['KeyMetadata']['KeyState'] == "PendingDeletion":
            logging.info(f"KMS Key Deletion Date: {kms_key_details['KeyMetadata']['DeletionDate']}")
            logging.info(f"KMS Key Pending Deletion In: {kms_key_details['KeyMetadata']['PendingDeletionWindowInDays']} days")
        logging.info(f"KMS Key Manager: {kms_key_details['KeyMetadata']['KeyManager']}")
        logging.info(f"KMS Key Origin: {kms_key_details['KeyMetadata']['Origin']}")
        if kms_key_details['KeyMetadata']['Origin'] == "EXTERNAL":
            logging.info(f"KMS Key Expiration Model: {kms_key_details['KeyMetadata']['ExpirationModel']}")
            if kms_key_details['KeyMetadata']['ExpirationModel'] == "KEY_MATERIAL_EXPIRES":
                logging.info(f"KMS Key Expiration Date: {kms_key_details['KeyMetadata']['ValidTo']}")
        logging.info(f"KMS Key Encryption Algorithms: {kms_key_details['KeyMetadata']['EncryptionAlgorithms']}")
        if kms_key_details['KeyMetadata']['KeyUsage'] == "SIGN_VERIFY":
            logging.info(f"KMS Key Signing Algorithms: {kms_key_details['KeyMetadata']['SigningAlgorithms']}")
        logging.info(f"KMS Key Multi Region Enabled: {kms_key_details['KeyMetadata']['MultiRegion']}")
        if kms_key_details['KeyMetadata']['MultiRegion'] == True:
            logging.info(f"KMS Key Multi Region Configuration Key Type: {kms_key_details['KeyMetadata']['MultiRegionConfiguration']['MultiRegionKeyType']}")
            logging.info(f"KMS Key Multi Region Configuration Primary Key ARN: {kms_key_details['KeyMetadata']['MultiRegionConfiguration']['PrimaryKey']['Arn']}")
            logging.info(f"KMS Key Multi Region Configuration Primary Key Region: {kms_key_details['KeyMetadata']['MultiRegionConfiguration']['PrimaryKey']['Region']}")
            logging.info(f"KMS Key Multi Region Configuration Replica Keys: {kms_key_details['KeyMetadata']['MultiRegionConfiguration']['ReplicaKeys']}")
        _print_kms_key_rotation_policy(kms_client=kms_client, kms_key_arn=kms_key_arn)
        _print_kms_key_alias(kms_client=kms_client, kms_key_arn=kms_key_arn)
        output.log_message_section("End of KMS Key Details", top=True, bottom=True)

        return 0

    except Exception as e:
        logging.error(f"Error printing KMS Key details: {e}")
        return 1


def _check_existing_kms_key_id(kms_client=None, kms_key_id=None):
    """ Check Existing KMS Key ID

    This internal function checks if a KMS Key ID already exists; if it does it returns the KMS Key ARN.

    This function is called by other publicly exposed functions in this module and is not intended to be called directly.

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

    This function is called by other publicly exposed functions in this module and is not intended to be called directly.

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


def _check_existing_kms_key_arn(kms_client=None, kms_key_arn=None):
    """Check Existing KMS Key ARN

    This function checks if a KMS Key ARN already exists; if it does it returns the KMS Key ID.

    This function is called by other publicly exposed functions in this module and is not intended to be called directly.

    Args:
        kms_client (boto3.client): A boto3 KMS client session
        kms_key_arn (str): A KMS Key ARN

    Returns:
        str: The KMS Key ID

    """
    try:
        logging.debug(f"Function: _check_existing_kms_key_arn() started with args: kms_client = {kms_client}, kms_key_arn = {kms_key_arn}")

        logging.info(f"Checking if KMS Key ARN {kms_key_arn} already exists")

        if kms_client == None:
            logging.error("No KMS Client provided")
            return 1

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        # Check if the KMS Key ARN already exists
        keys_list = kms_client.list_keys()
        for key in keys_list['Keys']:
            key_id = key['KeyId']
            key_arn = kms_client.describe_key(KeyId=key_id)['KeyMetadata']['Arn']
            if key_arn == kms_key_arn:
                logging.info(f"KMS Key ID {key_id} already exists")
                logging.debug(f"Function: _check_existing_kms_key_arn() completed")
                return key_arn

        logging.info(f"KMS Key ARN {kms_key_arn} does not exist")
        logging.debug(f"Function: _check_existing_kms_key_arn() completed")
        return False

    except Exception as e:
        logging.error(f"Unexpected error in _check_existing_kms_key_arn(): {e}")
        return 1


def _print_kms_key_alias(kms_client=None, kms_key_arn=None):
    """Get KMS Key Alias

    This function prints all KMS Key Aliases for a given KMS Key ARN.

    Args:
        kms_client (boto3.client): A boto3 KMS client session
        kms_key_arn (str): A KMS Key ARN

    Returns:
        int: 0 if successful, 1 if not

    Example:
        >>> _print_kms_key_alias(kms_client, "arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012")
        KMS Key Alias: alias/MyKeyAlias

    """
    try:
        logging.debug(f"Function: _print_kms_key_alias() started with args: kms_client = {kms_client}, kms_key_arn = {kms_key_arn}")

        if kms_client == None:
            logging.error("No KMS Client provided")
            return 1

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        key_aliases = kms_client.list_aliases(KeyId=kms_key_arn)
        # If there are one or more aliases for the KMS Key then print all allocated aliases
        if len(key_aliases['Aliases']) > 0:
            for key_alias in key_aliases['Aliases']:
                logging.info(f"KMS Key Alias: {key_alias['AliasName']}")
                logging.debug(f"Function: _print_kms_key_alias() completed")
                return 0

        logging.info(f"No KMS Key Alias found for KMS Key ARN: {kms_key_arn}")
        logging.debug(f"Function: _print_kms_key_alias() completed")
        return False

    except Exception as e:
        logging.error(f"Unexpected error in _print_kms_key_alias(): {e}")
        return 1


def _print_kms_key_rotation_policy(kms_client=None, kms_key_arn=None):
    """Print KMS Key Rotation Policy

    This function prints the KMS Key Rotation Policy for a given KMS Key ARN.

    Args:
        kms_client (boto3.client): A boto3 KMS client session
        kms_key_arn (str): A KMS Key ARN

    Returns:
        int: 0 if successful, 1 if not

    Example:
        >>> _print_kms_key_rotation_policy(kms_client, "arn:aws:kms:eu-west-1:123456789012:key/12345678-1234-1234-1234-123456789012")
        KMS Key Rotation Policy: {"AutomaticallyAfterDays": 30}

    """
    try:
        logging.debug(f"Function: _print_kms_key_rotation_policy() started with args: kms_client = {kms_client}, kms_key_arn = {kms_key_arn}")

        if kms_client == None:
            logging.error("No KMS Client provided")
            return 1

        if kms_key_arn == None:
            logging.error("No KMS Key ARN provided")
            return 1

        key_rotation_policy = kms_client.get_key_rotation_status(KeyId=kms_key_arn)

        if key_rotation_policy['KeyRotationEnabled'] == True:
            logging.info(f"KMS Key Rotation Policy: {key_rotation_policy['KeyRotationEnabled']} - KMS Key Rotation is enabled")
            logging.debug(f"Function: _print_kms_key_rotation_policy() completed")
            return 0

        if key_rotation_policy['KeyRotationEnabled'] == False:
            logging.info(f"KMS Key Rotation Policy: {key_rotation_policy['KeyRotationEnabled']} - KMS Key Rotation is disabled")
            logging.debug(f"Function: _print_kms_key_rotation_policy() completed")
            return 0

    except Exception as e:
        logging.error(f"Unexpected error in _print_kms_key_rotation_policy(): {e}")
        return 1