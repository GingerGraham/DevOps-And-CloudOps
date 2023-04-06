#!/usr/bin/env python3

"""S3 utilities
"""


# Import global modules
import logging
import sys

# Import local modules
import modules.output as output

# Import third party modules - see requirements.txt
from botocore.exceptions import ClientError, ParamValidationError


def check_existing_s3_bucket(aws_session=None, s3_client=None , s3_name=None, s3_region=None)):
    """Check if an S3 Bucket already exists

    This function checks if an S3 Bucket matching the required configuration already exists.

    Args:
        aws_session (session): AWS Session
        s3_name (str): Name of the S3 Bucket
        s3_region (str): Region of the S3 Bucket

    Returns:
        s3_arn (str): ARN of the S3 Bucket
        False if the S3 Bucket does not exist
        1 if an error occurs or the S3 Bucket is redirected or private
    """
    try:
        logging.debug(f"Function: check_existing_s3_bucket() started with args: aws_session={aws_session}, s3_client={s3_client}, s3_name={s3_name}, s3_region={s3_region}")

        if aws_session == None and s3_client == None:
            logging.error("No AWS Session or S3 Client provided")
            return 1

        if s3_name == None:
            logging.error("No S3 Bucket Name provided")
            return 1

        if s3_client == None and s3_region == None:
            s3_region = aws_session.region_name
            logging.warning(f"No S3 Bucket Region provided, using default region {s3_region}")

        if s3_client == None:
            s3_client = _create_s3_client(aws_session=aws_session, s3_region=s3_region)

        if s3_client == 1:
            logging.error(f"Error creating S3 Client")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return 1

        logging.info(f"Checking if S3 Bucket {s3_name} already exists in region {s3_region}")

        # Check if s3 bucket exists
        if s3_client.head_bucket(Bucket=s3_name):
            logging.debug(f"Bucket {s3_name} already exists")
            # Get arn of s3 bucket
            s3_arn = s3_client.get_bucket_acl(Bucket=s3_name)['Owner']['ID']
            logging.info(f"S3 Bucket {s3_name} already exists in region {s3_region}")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return s3_arn
        else:
            logging.debug(f"Bucket {s3_name} does not exist")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return False

    except ClientError as e:
        if e.response['Error']['Code'] == '301':
            logging.warning(f"[301] S3 Bucket {s3_name} is redirected and may already exist in another account")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return 1
        if e.response['Error']['Code'] == '403':
            logging.warning(f"[403] Private Bucket.  Forbidden access to S3 Bucket {s3_name}, may exist in another account")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return 1
        if e.response['Error']['Code'] == '404':
            logging.warning(f"[404] S3 Bucket {s3_name} does not exist")
            logging.debug(f"Function: check_existing_s3_bucket() completed")
            return False
        logging.error(f"Client Error in check_existing_s3_bucket: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in check_existing_s3_bucket: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in check_existing_s3_bucket: {sys.exc_info()[0]}")
        return 1


def create_s3_bucket(aws_session=None, s3_client=None, s3_name=None, s3_region=None, s3_versioning=True, s3_encryption=True, s3_kms_key_arn=None):


def _create_s3_client(aws_session=None, s3_region=None):
    """Create an S3 Client

    This function creates an S3 Client.

    Args:
        aws_session (session): AWS Session
        s3_region (str): Region of the S3 Bucket

    Returns:
        s3_client (client): S3 Client
        1 if an error occurs
    """
    try:
        logging.debug(f"Function: _create_s3_client() started with args: aws_session={aws_session}, s3_region={s3_region}")

        if aws_session == None:
            logging.error("No AWS Session provided")
            return 1

        if s3_region == None:
            s3_region = aws_session.region_name
            logging.warning(f"No S3 Bucket Region provided, using default region {s3_region}")

        # Create an S3 client from scratch not using the existing aws_session
        s3_client = aws_session.client('s3', region_name=s3_region)

        if s3_client == 1:
            logging.error(f"Error creating S3 Client")
            logging.debug(f"Function: _create_s3_client() completed")
            return 1

        logging.debug(f"Function: _create_s3_client() completed")
        return s3_client

    except ClientError as e:
        logging.error(f"Client Error in _create_s3_client: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in _create_s3_client: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in _create_s3_client: {sys.exc_info()[0]}")
        return 1


# Code below this line is legacy code that needs to be refactored

def _create_s3_bucket(args, aws_account_id, aws_session):
    """Create an S3 Bucket based on the passed arguments

    This function creates an S3 Bucket based on the passed arguments.

    Args:
        args (list): List of arguments passed from command line and parsed by argparse in _parse_args()
        aws_account_id (str): AWS Account ID
        aws_session (session): AWS Session

    Returns:
        s3_name (str): Name of the S3 Bucket
        s3_region (str): Region of the S3 Bucket
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
        output.log_message_section("S3 Bucket Configuration", top=True, bottom=True)
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
            _store_s3_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)
            return

        if args.list_only is True:
            logging.warning("List-only/dry-run is set, not creating S3 Bucket")
            _store_s3_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)
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
        _store_s3_details(args.bucket_name, args.bucket_region, args.bucket_kms_key_id, args.bucket_encryption, kms_key_id, kms_key_alias)

        # logging.debug("Function: _create_s3_bucket() completed")

    except AttributeError as e:
        logging.error(f"Attribute Error in _create_s3_bucket: {e}")
        return 1
    except ClientError as e:
        logging.error(f"Client Error in _create_s3_bucket: {e}")
        return 1
    except TypeError as e:
        logging.error(f"Type Error in _create_s3_bucket: {e}")
        return 1
    except UnboundLocalError as e:
        logging.error(f"Unbound Local Error in _create_s3_bucket: {e}")
        return 1
    except:
        logging.error(f"Unexpected error in _create_s3_bucket: {sys.exc_info()[0]}")
        return 1