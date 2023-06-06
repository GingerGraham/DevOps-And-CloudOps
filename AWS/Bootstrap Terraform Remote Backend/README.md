# Terraform Remote Backend Bootstrap

The purpose of this script/module is to bootstrap a Terraform remote backend on AWS S3.  This is a one-time operation that is required to use Terraform remote backend.  Once the remote backend is bootstrapped, you can use the remote backend to store the state of your Terraform infrastructure.

The created resources will also, optionally, create a DynamoDB table to store the state lock.  This is required to prevent multiple users from modifying the state at the same time.

- [Terraform Remote Backend Bootstrap](#terraform-remote-backend-bootstrap)
  - [Prerequisites](#prerequisites)
    - [Python Version](#python-version)
    - [Python Modules](#python-modules)
    - [AWS Credentials](#aws-credentials)
  - [Arguments / Command Line Options](#arguments--command-line-options)
  - [Usage](#usage)
    - [Output for use with Terraform](#output-for-use-with-terraform)
    - [Help Output](#help-output)
    - [Dry Run Example](#dry-run-example)

## Prerequisites

The following prerequisites are required to use this module:

### Python Version

- Python 3.6+

### Python Modules

- boto3
- botocore

These are included in the provided requirements.txt file and can be installed using pip:

```bash
pip install -r requirements.txt
```

### AWS Credentials

The AWS credentials must be configured in the environment.  The following environment variables are required:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION (optional)
- AWS_SESSION_TOKEN (optional)

These can be provided as environmental variables or in a credentials file.  See the [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) for more information.

## Arguments / Command Line Options

The following arguments are available:

| Argument | Description | Type | Default | Required |
|----------|-------------|------|---------|----------|
| aws_profile | AWS CLI profile to use for connection | string | default | no |
| region | AWS region to target | string | us-east-1 | no |
| bucket_name | Name for S3 Bucket| string | terraform-remote-state | no |
| bucket_region | Region for S3 Bucket | string | <same as AWS connection region> | no |
| bucket_versioning | Enable S3 Bucket Versioning? | boolean | True | no |
| bucket_encryption | Enable S3 Bucket Encryption? | boolean | True | no |
| bucket_kms_key_id | ID for existing KMS rather than create a new key | string | <none> | no |
| bucket_public_access_block | Block S3 Bucket Public Access? | boolean | True | no |
| dynamodb_table_enabled | Create DynamoDB Table for use as a Terraform backend lock table | boolean | True | no |
| dynamodb_table_name | Name for DynamoDB Table | string | terraform-remote-state | no |
| dynamodb_table_region | Region for DynamoDB Table | string | <same as AWS connection region> | no |
| dynamodb_table_read_capacity | DynamoDB Table Read Capacity | integer | 5 | no |
| dynamodb_table_write_capacity | DynamoDB Table Write Capacity | integer | 5 | no |
| log_file | Provide a file to save output to if desired | string | <none> | no |
| log_level | Log Level | string | INFO | no |
| list_only | List Only or Dry Run | boolean | False | no |

**Note:** Where names are provided for the S3 Bucket and DynamoDB Table the AWS Account ID will be appended automatically to the name.  This is to ensure that the bucket and table names are unique across all AWS accounts.

## Usage

The module can be used as a script or as a module.  The script is located in the `Bootstrap Terraform Remote Backend` directory; the script is named `terraform_remote_backend.py`.

### Output for use with Terraform

The script will print at the end of the script the values that are typically required for configuring a Terraform remote backend.  These values can be copied and pasted into a Terraform configuration file.

These are marked by the following header:

```bash
*******************************
S3 and DynamoDB Backend Details
Add the configuration below to your Terraform configuration!
************************************************************
```

Below the header the following values are printed:

- S3 Bucket Name
- S3 Bucket Region
- KMS Key ID (if a new key was created)
- KMS Key Alias
- DynamoDB Table Name

Example:

```bash
2023-03-09 09:16:51,676 [INFO] *******************************
2023-03-09 09:16:51,677 [INFO] S3 and DynamoDB Backend Details
2023-03-09 09:16:51,677 [INFO] Add the configuration below to your Terraform configuration!
2023-03-09 09:16:51,677 [INFO] ************************************************************
2023-03-09 09:16:51,678 [INFO] S3 Bucket Name: terraform-remote-state-404040186130
2023-03-09 09:16:51,679 [INFO] S3 Bucket Region: eu-west-2
2023-03-09 09:16:51,679 [INFO] KMS Key Alias: alias/terraform-remote-state-404040186130
2023-03-09 09:16:51,679 [INFO] DynamoDB Table Name: terraform-remote-state-404040186130
```

### Help Output

The script provides a full help output:

```bash
$ python terraform_remote_backend.py --help
```

```bash
python .\terraform-remote-bootstrap.py -h
usage: terraform-remote-bootstrap.py [-h] [--aws-profile AWS_PROFILE] [--region REGION] [--bucket-name BUCKET_NAME] [--bucket-region BUCKET_REGION] [--bucket-versioning BUCKET_VERSIONING] [--bucket-encryption BUCKET_ENCRYPTION] [--bucket-kms-key-id BUCKET_KMS_KEY_ID]
                                     [--bucket-public-access-block BUCKET_PUBLIC_ACCESS_BLOCK] [--dynamodb-table-enabled DYNAMODB_TABLE_ENABLED] [--dynamodb-table-name DYNAMODB_TABLE_NAME] [--dynamodb-table-region DYNAMODB_TABLE_REGION] [--dynamodb-table-read-capacity DYNAMODB_TABLE_READ_CAPACITY]
                                     [--dynamodb-table-write-capacity DYNAMODB_TABLE_WRITE_CAPACITY] [--log-file LOG_FILE] [--log-level LOG_LEVEL] [--list-only]

Terrform Remote Backend Bootstrap v1.0.1

options:
  -h, --help            show this help message and exit

AWS Connection Details:
  --aws-profile AWS_PROFILE, -a AWS_PROFILE
                        AWS Profile: default = default (Example: -a vcra-prod)
  --region REGION, -r REGION
                        AWS Region: default = us-east-1 (Example: -r eu-west-2)

S3 Bucket Details:
  --bucket-name BUCKET_NAME, -bn BUCKET_NAME
                        S3 Bucket Name: default = terraform-remote-state (Example: -bn terraform-remote-state)
  --bucket-region BUCKET_REGION, -br BUCKET_REGION
                        S3 Bucket Region: default = <same as AWS connection region> (Example: -br us-east-1)
  --bucket-versioning BUCKET_VERSIONING, -bv BUCKET_VERSIONING
                        S3 Bucket Versioning: default = True (Example: -bv False)
  --bucket-encryption BUCKET_ENCRYPTION, -be BUCKET_ENCRYPTION
                        S3 Bucket Encryption: default = True (Example: -be False)
  --bucket-kms-key-id BUCKET_KMS_KEY_ID, -bk BUCKET_KMS_KEY_ID
                        S3 Bucket KMS Key ID: default = <none> (Example: -bk 1234-5678-9012-3456-7890)
  --bucket-public-access-block BUCKET_PUBLIC_ACCESS_BLOCK, -bpb BUCKET_PUBLIC_ACCESS_BLOCK
                        S3 Bucket Public Access Block: default = True (Example: -bpb False)

DynamoDB Table Details:
  --dynamodb-table-enabled DYNAMODB_TABLE_ENABLED, -ddb DYNAMODB_TABLE_ENABLED
                        DynamoDB Table Enabled: default = True (Example: -ddb False)
  --dynamodb-table-name DYNAMODB_TABLE_NAME, -dt DYNAMODB_TABLE_NAME
                        DynamoDB Table Name: default = terraform-remote-state (Example: -dt terraform-remote-state)
  --dynamodb-table-region DYNAMODB_TABLE_REGION, -dr DYNAMODB_TABLE_REGION
                        DynamoDB Table Region: default = <same as AWS connection region> (Example: -dr us-east-1)
  --dynamodb-table-read-capacity DYNAMODB_TABLE_READ_CAPACITY, -drc DYNAMODB_TABLE_READ_CAPACITY
                        DynamoDB Table Read Capacity: default = 5 (Example: -drc 5)
  --dynamodb-table-write-capacity DYNAMODB_TABLE_WRITE_CAPACITY, -dwc DYNAMODB_TABLE_WRITE_CAPACITY
                        DynamoDB Table Write Capacity: default = 5 (Example: -dwc 5)

Log Options:
  --log-file LOG_FILE, -l LOG_FILE
                        Log file location (Example: -l /tmp/createAMI.log)
  --log-level LOG_LEVEL, -ll LOG_LEVEL
                        Log level: default = INFO (Example: -ll DEBUG)

Options:
  --list-only, -lo, --dry-run, --check, -C
                        [Flag] Dry run to list entities that would be created and exit without creating
```

### Dry Run Example

The following example shows a dry run of the script:

```bash
$ python terraform_remote_backend.py --list-only
```

Example using the `-C` flag alternative to `--list-only`:

```bash
python .\terraform-remote-bootstrap.py --region eu-west-2 -C
2023-03-09 09:16:49,344 [INFO] =========================================
2023-03-09 09:16:49,344 [INFO] Terraform Remote Backend Bootstrap v1.0.1
2023-03-09 09:16:49,344 [INFO] =========================================
2023-03-09 09:16:49,355 [INFO] Supplied Arguments
2023-03-09 09:16:49,355 [INFO] ==================
2023-03-09 09:16:49,355 [INFO] Aws Profile : default
2023-03-09 09:16:49,356 [INFO] Region : eu-west-2
2023-03-09 09:16:49,356 [INFO] Bucket Name : terraform-remote-state
2023-03-09 09:16:49,356 [INFO] Bucket Region : None
2023-03-09 09:16:49,357 [INFO] Bucket Versioning : True
2023-03-09 09:16:49,357 [INFO] Bucket Encryption : True
2023-03-09 09:16:49,358 [INFO] Bucket Kms Key Id : None
2023-03-09 09:16:49,358 [INFO] Bucket Public Access Block : True
2023-03-09 09:16:49,359 [INFO] Dynamodb Table Enabled : True
2023-03-09 09:16:49,359 [INFO] Dynamodb Table Name : terraform-remote-state
2023-03-09 09:16:49,361 [INFO] Dynamodb Table Region : None
2023-03-09 09:16:49,361 [INFO] Dynamodb Table Read Capacity : 5
2023-03-09 09:16:49,362 [INFO] Dynamodb Table Write Capacity : 5
2023-03-09 09:16:49,362 [INFO] Log File : None
2023-03-09 09:16:49,363 [INFO] Log Level : INFO
2023-03-09 09:16:49,363 [INFO] List Only : True
2023-03-09 09:16:49,364 [INFO] ===================
2023-03-09 09:16:49,365 [INFO] Connecting to AWS
2023-03-09 09:16:49,365 [INFO] Checking AWS CLI credentials
2023-03-09 09:16:49,367 [ERROR] AWS CLI credentials are not configured or profile default does not exist
2023-03-09 09:16:49,367 [INFO] AWS variables are set
2023-03-09 09:16:49,378 [INFO] AWS Session Details:
2023-03-09 09:16:49,379 [INFO] Profile: default
2023-03-09 09:16:49,379 [INFO] Region: eu-west-2
2023-03-09 09:16:49,515 [INFO] Found credentials in environment variables.
2023-03-09 09:16:50,205 [INFO] User: arn:aws:sts::404040186130:assumed-role/AWSReservedSSO_Administrator_5f69b5579a225d42/graham@roadtocloude.co.uk
2023-03-09 09:16:50,205 [INFO] Connected to AWS
2023-03-09 09:16:50,658 [INFO] Found credentials in environment variables.
2023-03-09 09:16:51,350 [INFO] KMS Key ID alias/terraform-remote-state-404040186130 does not exist, would create KMS Key ID alias/terraform-remote-state-404040186130
2023-03-09 09:16:51,350 [INFO] =======================
2023-03-09 09:16:51,350 [INFO] S3 Bucket Configuration
2023-03-09 09:16:51,350 [INFO] =======================
2023-03-09 09:16:51,350 [INFO] Bucket Name: terraform-remote-state-404040186130
2023-03-09 09:16:51,361 [INFO] Bucket Region: eu-west-2
2023-03-09 09:16:51,361 [INFO] Bucket KMS Key ID: None
2023-03-09 09:16:51,362 [INFO] Bucket KMS Key Alias: alias/terraform-remote-state-404040186130
2023-03-09 09:16:51,362 [INFO] Bucket Configuration: {'VersioningConfiguration': {'Status': 'Enabled'}, 'ServerSideEncryptionConfiguration': {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}}
2023-03-09 09:16:51,362 [INFO] Bucket Policy: {'PublicAccessBlockConfiguration': {'BlockPublicAcls': True, 'BlockPublicPolicy': True, 'IgnorePublicAcls': True, 'RestrictPublicBuckets': True}}
2023-03-09 09:16:51,363 [INFO] ===================
2023-03-09 09:16:51,363 [INFO] Checking if S3 Bucket terraform-remote-state-404040186130 already exists
2023-03-09 09:16:51,498 [INFO] S3 Bucket terraform-remote-state-404040186130 already exists
2023-03-09 09:16:51,504 [INFO] ============================
2023-03-09 09:16:51,505 [INFO] DynamoDB Table Configuration
2023-03-09 09:16:51,505 [INFO] ============================
2023-03-09 09:16:51,506 [INFO] DynamoDB Table Name: terraform-remote-state-404040186130
2023-03-09 09:16:51,506 [INFO] DynamoDB Table Region: eu-west-2
2023-03-09 09:16:51,506 [INFO] DynamoDB Table Read Capacity: 5
2023-03-09 09:16:51,507 [INFO] DynamoDB Table Write Capacity: 5
2023-03-09 09:16:51,507 [INFO] DynamoDB Primary Key: LockID
2023-03-09 09:16:51,507 [INFO] ========================================
2023-03-09 09:16:51,518 [INFO] Checking if DynamoDB Table terraform-remote-state-404040186130 already exists
2023-03-09 09:16:51,664 [INFO] DynamoDB Table terraform-remote-state-404040186130 already exists
2023-03-09 09:16:51,676 [INFO] *******************************
2023-03-09 09:16:51,677 [INFO] S3 and DynamoDB Backend Details
2023-03-09 09:16:51,677 [INFO] Add the configuration below to your Terraform configuration!
2023-03-09 09:16:51,677 [INFO] ************************************************************
2023-03-09 09:16:51,678 [INFO] S3 Bucket Name: terraform-remote-state-404040186130
2023-03-09 09:16:51,679 [INFO] S3 Bucket Region: eu-west-2
2023-03-09 09:16:51,679 [INFO] KMS Key Alias: alias/terraform-remote-state-404040186130
2023-03-09 09:16:51,679 [INFO] DynamoDB Table Name: terraform-remote-state-404040186130
2023-03-09 09:16:51,680 [INFO] =====================================
2023-03-09 09:16:51,680 [INFO] List only specified; NO CHANGES MADE!
2023-03-09 09:16:51,681 [INFO] =============================================
2023-03-09 09:16:51,681 [INFO] Terraform Remote Backend Bootstrap Completed!
```

### Example With Creation

The following example shows the output when the S3 bucket and DynamoDB table do not exist and are created.

```bash
python3 terraform-remote-bootstrap.py -r eu-west-2
2023-03-09 11:11:00,625 [INFO] =========================================
2023-03-09 11:11:00,625 [INFO] Terraform Remote Backend Bootstrap v1.0.1
2023-03-09 11:11:00,625 [INFO] =========================================
2023-03-09 11:11:00,626 [INFO] Supplied Arguments
2023-03-09 11:11:00,626 [INFO] ==================
2023-03-09 11:11:00,626 [INFO] Aws Profile : default
2023-03-09 11:11:00,626 [INFO] Region : eu-west-2
2023-03-09 11:11:00,626 [INFO] Bucket Name : terraform-remote-state
2023-03-09 11:11:00,626 [INFO] Bucket Region : None
2023-03-09 11:11:00,626 [INFO] Bucket Versioning : True
2023-03-09 11:11:00,626 [INFO] Bucket Encryption : True
2023-03-09 11:11:00,626 [INFO] Bucket Kms Key Id : None
2023-03-09 11:11:00,626 [INFO] Bucket Public Access Block : True
2023-03-09 11:11:00,626 [INFO] Dynamodb Table Enabled : True
2023-03-09 11:11:00,626 [INFO] Dynamodb Table Name : terraform-remote-state
2023-03-09 11:11:00,627 [INFO] Dynamodb Table Region : None
2023-03-09 11:11:00,627 [INFO] Dynamodb Table Read Capacity : 5
2023-03-09 11:11:00,627 [INFO] Dynamodb Table Write Capacity : 5
2023-03-09 11:11:00,628 [INFO] Log File : None
2023-03-09 11:11:00,629 [INFO] Log Level : INFO
2023-03-09 11:11:00,630 [INFO] List Only : False
2023-03-09 11:11:00,630 [INFO] ===================
2023-03-09 11:11:00,631 [INFO] Connecting to AWS
2023-03-09 11:11:00,631 [INFO] Checking AWS CLI credentials
2023-03-09 11:11:00,655 [INFO] AWS CLI credentials are configured and profile default exists
2023-03-09 11:11:00,718 [INFO] AWS Session Details:
2023-03-09 11:11:00,718 [INFO] Profile: default
2023-03-09 11:11:00,718 [INFO] Region: eu-west-2
2023-03-09 11:11:00,744 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2023-03-09 11:11:01,326 [INFO] User: arn:aws:iam::583007948674:user/gwatts
2023-03-09 11:11:01,328 [INFO] Connected to AWS
2023-03-09 11:11:01,882 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2023-03-09 11:11:02,199 [INFO] =======================
2023-03-09 11:11:02,199 [INFO] S3 Bucket Configuration
2023-03-09 11:11:02,199 [INFO] =======================
2023-03-09 11:11:02,199 [INFO] Bucket Name: terraform-remote-state-583007948674
2023-03-09 11:11:02,199 [INFO] Bucket Region: eu-west-2
2023-03-09 11:11:02,199 [INFO] Bucket KMS Key ID: None
2023-03-09 11:11:02,199 [INFO] Bucket KMS Key Alias: alias/terraform-remote-state-583007948674
2023-03-09 11:11:02,199 [INFO] Bucket Configuration: {'VersioningConfiguration': {'Status': 'Enabled'}, 'ServerSideEncryptionConfiguration': {'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}}
2023-03-09 11:11:02,199 [INFO] Bucket Policy: {'PublicAccessBlockConfiguration': {'BlockPublicAcls': True, 'BlockPublicPolicy': True, 'IgnorePublicAcls': True, 'RestrictPublicBuckets': True}}
2023-03-09 11:11:02,199 [INFO] ===================
2023-03-09 11:11:02,199 [INFO] Checking if S3 Bucket terraform-remote-state-583007948674 already exists
2023-03-09 11:11:02,417 [INFO] [404] S3 Bucket terraform-remote-state-583007948674 does not exist
2023-03-09 11:11:04,105 [INFO] ============================
2023-03-09 11:11:04,106 [INFO] DynamoDB Table Configuration
2023-03-09 11:11:04,106 [INFO] ============================
2023-03-09 11:11:04,106 [INFO] DynamoDB Table Name: terraform-remote-state-583007948674
2023-03-09 11:11:04,106 [INFO] DynamoDB Table Region: eu-west-2
2023-03-09 11:11:04,106 [INFO] DynamoDB Table Read Capacity: 5
2023-03-09 11:11:04,106 [INFO] DynamoDB Table Write Capacity: 5
2023-03-09 11:11:04,106 [INFO] DynamoDB Primary Key: LockID
2023-03-09 11:11:04,106 [INFO] ========================================
2023-03-09 11:11:04,129 [INFO] Checking if DynamoDB Table terraform-remote-state-583007948674 already exists
2023-03-09 11:11:04,374 [INFO] *******************************
2023-03-09 11:11:04,374 [INFO] S3 and DynamoDB Backend Details
2023-03-09 11:11:04,374 [INFO] Add the configuration below to your Terraform configuration!
2023-03-09 11:11:04,375 [INFO] ************************************************************
2023-03-09 11:11:04,375 [INFO] S3 Bucket Name: terraform-remote-state-583007948674
2023-03-09 11:11:04,375 [INFO] S3 Bucket Region: eu-west-2
2023-03-09 11:11:04,375 [INFO] KMS Key ID: 36924476-c6e2-42f7-a259-15fcf6d5ef27
2023-03-09 11:11:04,375 [INFO] KMS Key Alias: alias/terraform-remote-state-583007948674
2023-03-09 11:11:04,375 [INFO] DynamoDB Table Name: terraform-remote-state-583007948674
2023-03-09 11:11:04,375 [INFO] =============================================
2023-03-09 11:11:04,375 [INFO] Terraform Remote Backend Bootstrap Completed!
```
