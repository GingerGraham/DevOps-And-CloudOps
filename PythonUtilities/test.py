#!/usr/bin/env python3

# import ./modules/output.py as output
# Import output.py from ./modules
import modules.output as output
import modules.aws.connect as aws_connect
import modules.aws.dynamodb as dynamodb
import modules.aws.kms as kms

import logging
import sys

log_level=logging.INFO
log_format='%(asctime)s [%(levelname)s] %(message)s'
logging_file="C:\\Users\\watts\Temp\\test.log"

logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logging_file)
    ]
)

output.log_message_section("This is a message", top=True, bottom=True, divider="=")

profile = "default"
region = "eu-west-2"

aws_session = aws_connect.aws_connect(profile, region)

# dynamodb_table_name = "test"

# # db_exists = dynamodb.check_existing_dynamodb_table(aws_session=aws_session, dynamodb_table_name=dynamodb_table_name, dynamodb_table_region=region)
# db_exists = dynamodb.check_existing_dynamodb_table(aws_session=aws_session, dynamodb_table_name=dynamodb_table_name)
# logging.info(f"db_exists={db_exists}")

# if db_exists == False:
#     dynamodb_table_name = dynamodb.create_dynamodb_table(aws_session=aws_session, dynamodb_table_name=dynamodb_table_name, dynamodb_table_region=region)

# dynamodb.print_dynamobd_details(aws_session=aws_session, dynamodb_table_name=dynamodb_table_name, dynamodb_table_region=region)

kms_key_alias = "another_test_key"
key_exists = kms.check_existing_kms_key(aws_session=aws_session, kms_key_alias=kms_key_alias)
logging.info(f"key_exists={key_exists}")

if key_exists == False:
    kms_key_alias = kms.create_singleregion_encrypt_key(aws_session=aws_session, kms_key_alias=kms_key_alias)