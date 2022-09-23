# Query Lambda Script

The purpose of the query_lambdas script is to collate all lambda functions in one or more regions of a given AWS account and output the results to a CSV file.

The intention is to use this information to evaluate the current use of the functions including the current runtime and find any functions that are no longer in use or that require code updates.

## Required MacOS/Linux Command Line Tools

This script requires the following command line tools to be installed on the MacOS or Linux system:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [yq](https://github.com/mikefarah/yq)
- [jq](https://stedolan.github.io/jq/)

If these tools are missing the script will exit with an error message.

## Running the script

The script can be run from the command line directly from its subdirectory in the scripts directory of the repo.

The script will then prompt the following questions:

1. Does the user wish to use an AWS CLI profile, or enter the AWS credentials directly?
  1. If using a profile, which `profile` should be used?  A list of available profiles will be displayed.
  1. If using credentials the script will prompt for the `AWS Access Key ID`, and `AWS Secret Access Key`.
1. Does the user wish to use all regions (see [Regions](#regions) below), or enter a list of regions to use?
  1. If the user will provide a list of regions, the script will prompt for the regions to use and is expect a comma separated list of regions.

```bash
┌─(~/Development/Vocera/Bitbucket/DevOps/devops-mngt/scripts/QueryLambdas)────────────────────────────────────────────(grwatts@Graham-T480:s005)─┐
└─(13:54:27 on master ✹ ✭)──> ./query_aws_lambda.sh                                                                          130 ↵ ──(Wed,Sep07)─┘
2022-09-07 13:54:32 [INFO] Starting script
2022-09-07 13:54:32 [INFO] Checking for required applications
2022-09-07 13:54:32 [INFO] Required applications found
2022-09-07 13:54:32 [INFO] AWS Credentials found
2022-09-07 13:54:32 [INFO] AWS profiles found
2022-09-07 13:54:32 [INFO] Available profiles:
-------------------------
default
vcra-nonprod
vcra-prod
edge-prod
vcra-play
vcra-voip
vcra-alexa
-------------------------
2022-09-07 13:54:32 [INFO] Do you want to use a profile (default: no)? (y/n): y
2022-09-07 13:54:33 [INFO] Which profile do you want to use? (default: default): vcra-nonprod
2022-09-07 13:54:38 [INFO] Using profile: vcra-nonprod
2022-09-07 13:54:38 [INFO] Testing AWS connection using profile vcra-nonprod
2022-09-07 13:54:40 [INFO] AWS connection successful
2022-09-07 13:54:40 [INFO] Available regions
-------------------------
af-south-1
ap-east-1
ap-northeast-1
ap-northeast-2
ap-northeast-3
ap-south-1
ap-south-2
ap-southeast-1
ap-southeast-2
ap-southeast-3
ap-southeast-3
ap-southeast-4
ca-central-1
ca-west-1
cn-north-1
cn-northwest-1
eu-central-1
eu-central-2
eu-east-1
eu-north-1
eu-north-1
eu-south-1
eu-south-1
eu-west-1
eu-west-2
eu-west-3
me-south-1
me-south-2
me-west-1
ov-east-1
ov-secret-1
ov-topsecret-1
ov-topsecret-2
ov-west-1
ru-central-1
sa-east-1
us-east-1
us-east-2
us-west-1
us-west-2
-------------------------
Do you want to query all regions (default: no) ? (y/n): n
Please provide a list of regions to query (comma separated, default:us-east-1): us-east-1,us-east-2,us-east-5
2022-09-07 13:55:01 [ERROR] us-east-5 is not a valid region
2022-09-07 13:55:01 [INFO] Querying the following regions:
us-east-1
us-east-2
2022-09-07 13:55:02 [INFO] Querying AWS for Lambda functions using profile: vcra-nonprod
2022-09-07 13:55:02 [INFO] Querying us-east-1
2022-09-07 13:55:04 [INFO] Querying us-east-2
2022-09-07 13:55:06 [INFO] Creating CSV file
2022-09-07 13:55:06 [INFO] CSV file created
2022-09-07 13:55:07 [INFO] CSV file created: output/vcra-nonprod_2022-09-07_135501/vcra-nonprod_lambda_functions_.csv
2022-09-07 13:55:07 [INFO] Script complete
```

## Connection to AWS Account

Connection details can be drawn either from configured AWS CLI from the ~/.aws/credentials file or will be prompted for by the script.

The connection will be tested for success before the script continues

## Regions

As supplied in the repo there is an all_regions.yml file containing all of the AWS regions as of 2022-09-06.  This file can be edited if desired to add or remove regions.

Where available the all_regions.yml file serves 2 purposes:

1. To provide a full lists of regions which can be queried
1. To validate user input for regions

## Queried Fields

By default the script queries the following fields from each lambda function description into the CSV file:

- FunctionName
- FunctionArn
- Runtime
- LastModified

This can be modified by changing the script variable `REQUIRED_FIELDS` to include or exclude fields as required.  This variable is an array of strings.

## Output

This script will create a child directory in the `./output` directory of the current directory of the repo.  The name of the directory will be either the `profile` name from the AWS CLI config or the `Access Key ID` provided to connect to the account followed by the date and time of the script execution; e.g. `vcra-nonprod_2022-09-06_165052`.

In the output directory the script will create a JSON file with full details on the lambdas in the account/region for each region queried where a response was provided.  Regions that can be connected to, but have no lambdas will create a JSON file with an empty array.  Regions that cannot be connected to will not create a JSON file.

Finally; the script will create a single CSV file containing the requested information for all of the lambdas found across all queried regions in the account.

### Output Examples

```bash
# Example directory structure
.
├── output
│   └── vcra-nonprod_2022-09-06_165006
│       ├── lambda_functions_vcra-nonprod_ap-northeast-1_2022-09-06_165010.json
│       ├── lambda_functions_vcra-nonprod_ap-northeast-2_2022-09-06_165013.json
│       ├── lambda_functions_vcra-nonprod_ap-northeast-3_2022-09-06_165015.json
│       ├── lambda_functions_vcra-nonprod_ap-south-1_2022-09-06_165017.json
│       ├── lambda_functions_vcra-nonprod_ap-southeast-1_2022-09-06_165020.json
│       ├── lambda_functions_vcra-nonprod_ap-southeast-2_2022-09-06_165024.json
│       ├── lambda_functions_vcra-nonprod_ca-central-1_2022-09-06_165034.json
│       ├── lambda_functions_vcra-nonprod_eu-central-1_2022-09-06_165045.json
│       ├── lambda_functions_vcra-nonprod_eu-north-1_2022-09-06_165105.json
│       ├── lambda_functions_vcra-nonprod_eu-north-1_2022-09-06_165107.json
│       ├── lambda_functions_vcra-nonprod_eu-west-1_2022-09-06_165111.json
│       ├── lambda_functions_vcra-nonprod_eu-west-2_2022-09-06_165113.json
│       ├── lambda_functions_vcra-nonprod_eu-west-3_2022-09-06_165114.json
│       ├── lambda_functions_vcra-nonprod_sa-east-1_2022-09-06_165729.json
│       ├── lambda_functions_vcra-nonprod_us-east-1_2022-09-06_165732.json
│       ├── lambda_functions_vcra-nonprod_us-east-2_2022-09-06_165735.json
│       ├── lambda_functions_vcra-nonprod_us-west-1_2022-09-06_165736.json
│       ├── lambda_functions_vcra-nonprod_us-west-2_2022-09-06_165738.json
│       └── vcra-nonprod_lambda_functions_.csv
```

```bash
# Example CSV file
FunctionName,FunctionArn,Runtime,LastModified,LastUpdateStatus
"Guardduty_toslack","arn:aws:lambda:ap-south-1:570346948435:function:Guardduty_toslack","python2.7","2021-02-11T08:01:03.981+0000",
"guard_duty_3","arn:aws:lambda:ap-south-1:570346948435:function:guard_duty_3","python3.7","2021-02-11T08:00:34.032+0000",
```

```json
# Example JSON file
{
    "Functions": [
        {
            "FunctionName": "GuardDuty_Slack",
            "FunctionArn": "arn:aws:lambda:us-east-2:570346948435:function:GuardDuty_Slack",
            "Runtime": "python2.7",
            "Role": "arn:aws:iam::570346948435:role/lambda_basic_execution",
            "Handler": "guarddutyalert.lambda_handler",
            "CodeSize": 3867002,
            "Description": "",
            "Timeout": 3,
            "MemorySize": 128,
            "LastModified": "2019-04-10T17:55:15.983+0000",
            "CodeSha256": "UZjQ5pHcYcquDmqNtjqdxMKpaD7rMp9igyC3i4uGCaE=",
            "Version": "$LATEST",
            "VpcConfig": {
                "SubnetIds": [],
                "SecurityGroupIds": [],
                "VpcId": ""
            },
            "Environment": {
                "Variables": {
                    "AWS_ACCOUNT": "AWS Nonprod [N. Virginia]",
                    "HOOK_URL": "https://hooks.slack.com/services/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"
                }
            },
            "TracingConfig": {
                "Mode": "PassThrough"
            },
            "RevisionId": "fef316d3-2cb8-4b2a-8931-f3439c1110d3",
            "PackageType": "Zip",
            "Architectures": [
                "x86_64"
            ],
            "EphemeralStorage": {
                "Size": 512
            }
        },
        {
            "FunctionName": "VCESentiments-DatalakeSta-MLQuickStartWebResourceD-1ER8IATVDM3NT",
            "FunctionArn": "arn:aws:lambda:us-east-2:570346948435:function:VCESentiments-DatalakeSta-MLQuickStartWebResourceD-1ER8IATVDM3NT",
            "Runtime": "python2.7",
            "Role": "arn:aws:iam::570346948435:role/VCESentiments-DatalakeStack-15-LambdaExecutionRole-1IS63TPZR0J2W",
            "Handler": "index.handler",
            "CodeSize": 1375,
            "Description": "",
            "Timeout": 30,
            "MemorySize": 128,
            "LastModified": "2018-08-14T21:43:28.148+0000",
            "CodeSha256": "U9p7MaiHRbXkDHvn6sqHNG9w8xDiAqKntspifzVUabg=",
            "Version": "$LATEST",
            "TracingConfig": {
                "Mode": "PassThrough"
            },
            "RevisionId": "419db73e-d43d-4b76-8e00-dbb222758d88",
            "PackageType": "Zip",
            "Architectures": [
                "x86_64"
            ],
            "EphemeralStorage": {
                "Size": 512
            }
        },
    ]
}
```

