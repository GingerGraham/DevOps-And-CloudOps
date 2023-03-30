#!/usr/bin/env python3

"""KMS utilities
"""

# Import global modules
import logging

# To do
# - Add a function to check if a KMS Key ID already exists - determine what we should return if it does exist
# - Add a function to create a KMS Key ID
# - Add an internal function to create a boto3 kms client session
# - Add a function to print the details of a KMS Key ID to logging.info

def check_existing_kms_key(aws_session=None, kms_client=None, kms_key_region=None, kms_key_alias=None):
    """Check Existing KMS Key
    """
    try:
        # Check if the KMS Key ID already exists
        if kms_key_alias is None:
            logging.error("KMS Key Alias not provided")
            return False

        # Check if the KMS Key Alias already exists
        keys_list = kms_client.list_keys()
        for key in keys_list['Keys']:
            key_id = key['KeyId']
            key_arn = kms_client.describe_key(KeyId=key_id)['KeyMetadata']['Arn']
            key_aliases = kms_client.list_aliases(KeyId=key_id)
            for key_alias in key_aliases['Aliases']:
                if key_alias['AliasName'] == kms_key_alias:
                    logging.info("KMS Key ID {0} already exists".format(key_id))
                    return True
        return False


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