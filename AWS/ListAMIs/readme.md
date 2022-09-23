# List AMIs Utility

This script utility is designed to list AMIs in a given region. It can be used to list all AMIs or a subset of AMIs based on a filter.

AMI Images can be found in the AWS Console under EC2 --> Images --> AMIs.

## Running the script

The script can be run from the command line using the following command:

```bash
./ListAMIs.py
```

The script takes a number of [parameters](#parameters) that can be provided in the command line all parameters are optional and where applicable default values are provided.

### Connecting to AWS

This script requires the AWS CLI to be [setup and configured](https://vocera.atlassian.net/wiki/spaces/VD/pages/1683521812/AWS+CLI) with a mimimum of the [`default` profile](https://vocera.atlassian.net/wiki/spaces/VD/pages/1683521812/AWS+CLI#Configuring-a-default-profile) configured.  [Named profiles](https://vocera.atlassian.net/wiki/spaces/VD/pages/1683521812/AWS+CLI#More-on-named-profiles) are supported using the `--aws-profile` parameter.

### Parameters

```bash
 ./ListAMIs.py --help                                                                                                                   ──(Mon,Sep12)─┘
usage: ListAMIs.py [-h] [--aws-profile AWS_PROFILE] [--region REGION] [--product PRODUCT] [--environment ENVIRONMENT] [--tenant TENANT] [--role ROLE] [--owner OWNER]
                   [--name NAME] [--extra-tags EXTRA_TAGS] [--instance-ids INSTANCE_IDS] [--log-file LOG_FILE] [--log-level LOG_LEVEL] [--no-save] [--format FORMAT]
                   [--filename FILENAME] [--output-dir OUTPUT_DIR] [--verbose | --silent]

AWS EC2 AMI Reporting

options:
  -h, --help            show this help message and exit
  --verbose, -v         Verbose output
  --silent, -s          Do not display AMI details

AWS Connection Details:
  --aws-profile AWS_PROFILE, -a AWS_PROFILE
                        AWS Profile: default = default
  --region REGION, -r REGION
                        AWS Region: default = us-east-1

Instance Details (Tags and/or Instance IDs):
  --product PRODUCT, -p PRODUCT
                        EC2 Instance Product Tag
  --environment ENVIRONMENT, -e ENVIRONMENT
                        EC2 Instance Environment Tag
  --tenant TENANT, -t TENANT
                        EC2 Instance Tenant Tag
  --role ROLE, -rl ROLE
                        EC2 Instance Role Tag
  --owner OWNER, -o OWNER
                        EC2 Instance Owner Tag
  --name NAME, -n NAME  EC2 Instance Name Tag
  --extra-tags EXTRA_TAGS, -x EXTRA_TAGS
                        Other tags that can be used to search for AMI images as a comma separated key=value list (Example: -x key1=value1,key2=value2)
  --instance-ids INSTANCE_IDS, -i INSTANCE_IDS
                        Instance IDs to create AMI from as a comma separated list

Log Options:
  --log-file LOG_FILE, -l LOG_FILE
                        Log file location
  --log-level LOG_LEVEL, -ll LOG_LEVEL
                        Log level: default = INFO

Output Options:
  --no-save, -ns        Do not save list of AMIs
  --format FORMAT, -fm FORMAT
                        Output format. Accepted values: csv (default), json, yaml
  --filename FILENAME, -f FILENAME
                        File name for output: default = AMI-Report-<aws_profile>-<region>-<date>_<timestamp>.csv
  --output-dir OUTPUT_DIR, -d OUTPUT_DIR
                        Directory to store output files: default = current directory
```

All parameters are optional; however the following defaults are used if not provided:

- `--aws-profile`: `default`
- `--region`: `us-east-1`
- `--log-level`: `INFO`
- `--log-file`: None - log only to the console
- `--no-save`: False
- `--format`: `csv`
- `--filename`: `AMI-Report-<aws_profile>-<region>-<date>_<timestamp>.csv`
- `--output-dir`: `.` - current directory

The following limitations or requirements apply to the parameters:

**Note:** wildcards are not supported

- `--aws-profile`: Accepts a single profile name (e.g. `default` or `my-profile`)
- `--region`: Accepts a single region (e.g. `us-east-1` or `us-west-2`)
- `--product`: Accepts a single product tag (e.g. `product-1` or `product-2`)
- `--environment`: Accepts a single environment tag (e.g. `environment-1` or `environment-2`)
- `--tenant`: Accepts a single tenant tag (e.g. `tenant-1` or `tenant-2`)
- `--role`: Accepts a single role tag (e.g. `role-1` or `role-2`)
- `--owner`: Accepts a single owner tag (e.g. `me` or `you`)
- `--name`: Accepts a single name tag (e.g. `my-instance` or `your-instance`)
- `--instance-ids`: Accepts a comma separated list of instance IDs (e.g. `i-123456789,i-987654321`)
- `--extra-tags`: Accepts a comma separated list of key=value pairs (e.g. `custom=test,name=my-instance`)
- `--log-file`: Requires a single log file path including file name and extension (e.g. `/tmp/log.txt`)
- `--log-level`: Accepts a single log level (e.g. `INFO` or `DEBUG`)
- `--verbose`: Mutually exclusive with `--silent`. Does **not** accept a value, this is a flag.  Including the flag will cause the script to generate a verbose output of all actions including detailed information on each AMI image being printed to the console.  This may be too much detail for wide search criteria (such as no tags) and may cause the script output to overrun the console buffer, consider using `--log-file` to redirect output to a file for further review.
- `--silent`: Mutually exclusive with `--verbose`. Does **not** accept a value, this is a flag.  Including the flag will cause the script to generate minimal output to the console or log and is useful for minimising console output while generating a saved report file.
- `--no-save`: Does **not** accept a value, this is a flag.  Including the flag will cause the script to not save the report file.  This is useful for generating a report to the console or log only.
- `--format`: Accepts a single format (e.g. `csv` or `json`)
- `--filename`: Requires a single string to be used as a file name excluding extension (e.g. `my-report`).  The extension will be added based on the `--format` parameter.
- `--output-dir`: Requires a single directory path (e.g. `/tmp` or `C:\Temp`)

**Note:** `--instance-ids` is used to add additional instances to the list of instances to have AMI images created from.  This is useful for adding additional instances over and above any that are found using the supplied tags.
**Note:** `--extra-tags` is used to further filter the search for instances and is added to the filter list alongside `--product`, `--environment`, `--tenant`, `--role`, `--owner`, and `--name`.  This is useful if the tag(s) you require are not covered by this scripts parameters.

### Logging

By default logging is set to `INFO` level logging and does not log to a file (log file = `/dev/null`).

The behaviour can be changed with the following parameters:

- `--log-file` or `-l`: The location of the log file.
- `--log-level` or `-ll`: The log level.

### Examples

#### Running a region wide query of AP-South-1 with no tags


```bash
┌─(~/Development/Vocera/Bitbucket/DevOps/devops-mngt/scripts/ListAMIs)─────────────────────────────────────────────────────────────────────────────────(grwatts@MacBook-Pro:s004)─┐
└─(10:00:27 on master↑ ✭)──> ./ListAMIs.py  --aws-profile vcra-nonprod --region ap-south-1 --output-dir /tmp/                                                   1 ↵ ──(Mon,Sep12)─┘
2022-09-12 10:00:37,559 [INFO] ===================
2022-09-12 10:00:37,560 [INFO] AMI Image Report
2022-09-12 10:00:37,560 [INFO] ===================
2022-09-12 10:00:37,560 [INFO] Supplied arguments
2022-09-12 10:00:37,560 [INFO] ===================
2022-09-12 10:00:37,560 [INFO] Aws Profile : vcra-nonprod
2022-09-12 10:00:37,560 [INFO] Region : ap-south-1
2022-09-12 10:00:37,560 [INFO] Product : None
2022-09-12 10:00:37,560 [INFO] Environment : None
2022-09-12 10:00:37,560 [INFO] Tenant : None
2022-09-12 10:00:37,560 [INFO] Role : None
2022-09-12 10:00:37,560 [INFO] Owner : None
2022-09-12 10:00:37,560 [INFO] Name : None
2022-09-12 10:00:37,561 [INFO] Extra Tags : None
2022-09-12 10:00:37,561 [INFO] Instance Ids : None
2022-09-12 10:00:37,561 [INFO] Log File : None
2022-09-12 10:00:37,561 [INFO] Log Level : INFO
2022-09-12 10:00:37,561 [INFO] No Save : False
2022-09-12 10:00:37,561 [INFO] Format : csv
2022-09-12 10:00:37,561 [INFO] Filename : AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_090037-UTC
2022-09-12 10:00:37,561 [INFO] Output Dir : /tmp
2022-09-12 10:00:37,561 [INFO] Verbose : False
2022-09-12 10:00:37,562 [INFO] Silent : False
2022-09-12 10:00:37,562 [INFO] ===================
2022-09-12 10:00:37,577 [INFO] Connected to AWS
2022-09-12 10:00:37,577 [INFO] ===================
2022-09-12 10:00:37,578 [INFO] Searching for AMIs
2022-09-12 10:00:37,625 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2022-09-12 10:00:38,775 [INFO] ===================
2022-09-12 10:00:38,776 [INFO] Found 9 AMI images
2022-09-12 10:00:38,776 [INFO] ===================
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0cdefb106289891ce, Name: import-ami-0c0c8aca7f66c538a, Created Date: 2022-06-22T11:36:30.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0e4ab8d6517d60e35, Name: import-ami-0b523b19b0e7c758d, Created Date: 2022-06-22T11:49:44.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-08ae657a993f9e557, Name: import-ami-0d465e9842759cc02, Created Date: 2022-06-23T04:48:54.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0b9927621aaf6d8f2, Name: import-ami-088c54f5fa1de9647, Created Date: 2022-06-23T09:19:54.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0c307765e4c64b800, Name: ansible-dev-server-updated-ami-aws, Created Date: 2022-07-08T05:35:46.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0acad0bea38cac890, Name: vocera-edge-server-4.x-oracle-8.4-05, Created Date: 2022-07-12T01:09:40.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0ca9c9bc53df31186, Name: import-ami-01f2cfd300d5f9d68, Created Date: 2022-08-01T08:24:11.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-01c26ec5cb518b630, Name: edge-test-4.x-installed-amibackup, Created Date: 2022-08-03T08:04:19.000Z
2022-09-12 10:00:38,776 [INFO] ImageId: ami-0987e783e28a35177, Name: vocera-edge-server-4.x-oracle-8.6-08, Created Date: 2022-08-08T17:04:10.000Z
2022-09-12 10:00:38,776 [INFO] Saving output in csv format
2022-09-12 10:00:38,776 [INFO] Creating /tmp/AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_090037-UTC.csv
2022-09-12 10:00:38,777 [INFO] File created successfully
2022-09-12 10:00:38,778 [INFO] File saved to /tmp/AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_090037-UTC.csv
2022-09-12 10:00:38,778 [INFO] ===================
2022-09-12 10:00:38,778 [INFO] Found 9 AMI images
2022-09-12 10:00:38,778 [INFO] ===================
2022-09-12 10:00:38,778 [INFO] Script Complete
```

#### Running a region wide query of AP-South-1 with no tags with the silent flag

```bash
┌─(~/Development/Vocera/Bitbucket/DevOps/devops-mngt/scripts/ListAMIs)─────────────────────────────────────────────────────────────────────────────────(grwatts@MacBook-Pro:s004)─┐
└─(10:15:16 on master↑ ✭)──> ./ListAMIs.py  --aws-profile vcra-nonprod --region ap-south-1 --output-dir /tmp/ --silent                                              ──(Mon,Sep12)─┘
2022-09-12 10:16:38,595 [INFO] ===================
2022-09-12 10:16:38,595 [INFO] AMI Image Report
2022-09-12 10:16:38,595 [INFO] ===================
2022-09-12 10:16:38,595 [WARNING] Silent mode enabled. Minimal output only will be displayed.
2022-09-12 10:16:38,673 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2022-09-12 10:16:39,927 [INFO] File saved to /tmp/AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_091638-UTC.csv
```

#### Running a region wide query of AP-South-1 with no tags with the verbose flag

```bash
┌─(~/Development/Vocera/Bitbucket/DevOps/devops-mngt/scripts/ListAMIs)─────────────────────────────────────────────────────────────────────────────────(grwatts@MacBook-Pro:s004)─┐
└─(10:16:53 on master↑ ✭)──> ./ListAMIs.py  --aws-profile vcra-nonprod --region ap-south-1 --output-dir /tmp/ --verbose                                             ──(Mon,Sep12)─┘
2022-09-12 10:17:08,573 [INFO] ===================
2022-09-12 10:17:08,574 [INFO] AMI Image Report
2022-09-12 10:17:08,574 [INFO] ===================
2022-09-12 10:17:08,574 [INFO] Supplied arguments
2022-09-12 10:17:08,574 [INFO] ===================
2022-09-12 10:17:08,574 [INFO] Aws Profile : vcra-nonprod
2022-09-12 10:17:08,574 [INFO] Region : ap-south-1
2022-09-12 10:17:08,575 [INFO] Product : None
2022-09-12 10:17:08,575 [INFO] Environment : None
2022-09-12 10:17:08,575 [INFO] Tenant : None
2022-09-12 10:17:08,575 [INFO] Role : None
2022-09-12 10:17:08,575 [INFO] Owner : None
2022-09-12 10:17:08,575 [INFO] Name : None
2022-09-12 10:17:08,575 [INFO] Extra Tags : None
2022-09-12 10:17:08,575 [INFO] Instance Ids : None
2022-09-12 10:17:08,575 [INFO] Log File : None
2022-09-12 10:17:08,575 [INFO] Log Level : INFO
2022-09-12 10:17:08,575 [INFO] No Save : False
2022-09-12 10:17:08,575 [INFO] Format : csv
2022-09-12 10:17:08,575 [INFO] Filename : AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_091708-UTC
2022-09-12 10:17:08,575 [INFO] Output Dir : /tmp
2022-09-12 10:17:08,576 [INFO] Verbose : True
2022-09-12 10:17:08,576 [INFO] Silent : False
2022-09-12 10:17:08,576 [INFO] ===================
2022-09-12 10:17:08,576 [INFO] Connecting to AWS
2022-09-12 10:17:08,591 [INFO] Connected to AWS
2022-09-12 10:17:08,591 [INFO] Session Details: Session(region_name='ap-south-1')
2022-09-12 10:17:08,591 [INFO] ===================
2022-09-12 10:17:08,591 [INFO] Filters: []
2022-09-12 10:17:08,591 [INFO] Searching for AMIs
2022-09-12 10:17:08,639 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2022-09-12 10:17:09,836 [INFO] ===================
2022-09-12 10:17:09,836 [INFO] Found 9 AMI images
2022-09-12 10:17:09,837 [INFO] ===================
2022-09-12 10:17:09,837 [INFO] ImageId: ami-0cdefb106289891ce
2022-09-12 10:17:09,837 [INFO] Name: import-ami-0c0c8aca7f66c538a
2022-09-12 10:17:09,837 [INFO] Description: AWS-VMImport service: Linux - CentOS release 6.10 (Final) - 2.6.32-754.35.1.el6.x86_64
2022-09-12 10:17:09,837 [INFO] CreationDate: 2022-06-22T11:36:30.000Z
2022-09-12 10:17:09,837 [INFO] State: available
2022-09-12 10:17:09,837 [INFO] Architecture: x86_64
2022-09-12 10:17:09,837 [INFO] ImageType: machine
2022-09-12 10:17:09,837 [INFO] Hypervisor: xen
2022-09-12 10:17:09,837 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,837 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,837 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-green-qa-imported-ami'}]
2022-09-12 10:17:09,837 [INFO] ===================
2022-09-12 10:17:09,837 [INFO] ImageId: ami-0e4ab8d6517d60e35
2022-09-12 10:17:09,838 [INFO] Name: import-ami-0b523b19b0e7c758d
2022-09-12 10:17:09,838 [INFO] Description: AWS-VMImport service: Linux - Oracle Linux Server 8.5 - 4.18.0-348.7.1.el8_5.x86_64
2022-09-12 10:17:09,838 [INFO] CreationDate: 2022-06-22T11:49:44.000Z
2022-09-12 10:17:09,838 [INFO] State: available
2022-09-12 10:17:09,838 [INFO] Architecture: x86_64
2022-09-12 10:17:09,838 [INFO] ImageType: machine
2022-09-12 10:17:09,838 [INFO] Hypervisor: xen
2022-09-12 10:17:09,838 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,838 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,838 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-silver-qa-imported-ami'}]
2022-09-12 10:17:09,838 [INFO] ===================
2022-09-12 10:17:09,838 [INFO] ImageId: ami-08ae657a993f9e557
2022-09-12 10:17:09,838 [INFO] Name: import-ami-0d465e9842759cc02
2022-09-12 10:17:09,838 [INFO] Description: AWS-VMImport service: Linux - CentOS Linux 7 (Core) - 3.10.0-1127.13.1.el7.x86_64
2022-09-12 10:17:09,838 [INFO] CreationDate: 2022-06-23T04:48:54.000Z
2022-09-12 10:17:09,839 [INFO] State: available
2022-09-12 10:17:09,839 [INFO] Architecture: x86_64
2022-09-12 10:17:09,839 [INFO] ImageType: machine
2022-09-12 10:17:09,839 [INFO] Hypervisor: xen
2022-09-12 10:17:09,839 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,839 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,839 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-ansible-imported-ami'}]
2022-09-12 10:17:09,839 [INFO] ===================
2022-09-12 10:17:09,839 [INFO] ImageId: ami-0b9927621aaf6d8f2
2022-09-12 10:17:09,839 [INFO] Name: import-ami-088c54f5fa1de9647
2022-09-12 10:17:09,839 [INFO] Description: AWS-VMImport service: Linux - CentOS release 6.10 (Final) - 2.6.32-754.35.1.el6.x86_64
2022-09-12 10:17:09,839 [INFO] CreationDate: 2022-06-23T09:19:54.000Z
2022-09-12 10:17:09,839 [INFO] State: available
2022-09-12 10:17:09,839 [INFO] Architecture: x86_64
2022-09-12 10:17:09,839 [INFO] ImageType: machine
2022-09-12 10:17:09,840 [INFO] Hypervisor: xen
2022-09-12 10:17:09,840 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,840 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,840 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-byod41-imported-ami'}]
2022-09-12 10:17:09,840 [INFO] ===================
2022-09-12 10:17:09,840 [INFO] ImageId: ami-0c307765e4c64b800
2022-09-12 10:17:09,840 [INFO] Name: ansible-dev-server-updated-ami-aws
2022-09-12 10:17:09,840 [INFO] Description: ami created after copying the Yum content from Onprem
2022-09-12 10:17:09,840 [INFO] CreationDate: 2022-07-08T05:35:46.000Z
2022-09-12 10:17:09,840 [INFO] State: available
2022-09-12 10:17:09,840 [INFO] Architecture: x86_64
2022-09-12 10:17:09,840 [INFO] ImageType: machine
2022-09-12 10:17:09,840 [INFO] Hypervisor: xen
2022-09-12 10:17:09,840 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,840 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,840 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-ansible-dev-server-updated-ami-aws'}]
2022-09-12 10:17:09,841 [INFO] ===================
2022-09-12 10:17:09,841 [INFO] ImageId: ami-0acad0bea38cac890
2022-09-12 10:17:09,841 [INFO] Name: vocera-edge-server-4.x-oracle-8.4-05
2022-09-12 10:17:09,841 [INFO] Description: [Copied ami-078a9c1e7f8d428c8 (vocera-edge-server-4.x-oracle-8.4-05) from us-east-1] vocera-edge-server-4.x-oracle-8.4-05.ova
2022-09-12 10:17:09,841 [INFO] CreationDate: 2022-07-12T01:09:40.000Z
2022-09-12 10:17:09,841 [INFO] State: available
2022-09-12 10:17:09,841 [INFO] Architecture: x86_64
2022-09-12 10:17:09,841 [INFO] ImageType: machine
2022-09-12 10:17:09,841 [INFO] Hypervisor: xen
2022-09-12 10:17:09,841 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,841 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,841 [INFO] Tags: [{'Key': 'Name', 'Value': 'vocera-edge-server-4.x-oracle-8.4-05'}]
2022-09-12 10:17:09,841 [INFO] ===================
2022-09-12 10:17:09,841 [INFO] ImageId: ami-0ca9c9bc53df31186
2022-09-12 10:17:09,841 [INFO] Name: import-ami-01f2cfd300d5f9d68
2022-09-12 10:17:09,842 [INFO] Description: AWS-VMImport service: Linux - Debian GNU/Linux 8 (jessie) - 3.16.0-4-amd64
2022-09-12 10:17:09,842 [INFO] CreationDate: 2022-08-01T08:24:11.000Z
2022-09-12 10:17:09,842 [INFO] State: available
2022-09-12 10:17:09,842 [INFO] Architecture: x86_64
2022-09-12 10:17:09,842 [INFO] ImageType: machine
2022-09-12 10:17:09,842 [INFO] Hypervisor: xen
2022-09-12 10:17:09,842 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,842 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,842 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-freeswitch'}]
2022-09-12 10:17:09,842 [INFO] ===================
2022-09-12 10:17:09,842 [INFO] ImageId: ami-01c26ec5cb518b630
2022-09-12 10:17:09,842 [INFO] Name: edge-test-4.x-installed-amibackup
2022-09-12 10:17:09,842 [INFO] Description: edge-test-4.x-installed-amibackup
2022-09-12 10:17:09,842 [INFO] CreationDate: 2022-08-03T08:04:19.000Z
2022-09-12 10:17:09,842 [INFO] State: available
2022-09-12 10:17:09,843 [INFO] Architecture: x86_64
2022-09-12 10:17:09,843 [INFO] ImageType: machine
2022-09-12 10:17:09,843 [INFO] Hypervisor: xen
2022-09-12 10:17:09,843 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,843 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,843 [INFO] Tags: [{'Key': 'Name', 'Value': 'edge-test-4.x-installed-amibackup'}]
2022-09-12 10:17:09,843 [INFO] ===================
2022-09-12 10:17:09,843 [INFO] ImageId: ami-0987e783e28a35177
2022-09-12 10:17:09,843 [INFO] Name: vocera-edge-server-4.x-oracle-8.6-08
2022-09-12 10:17:09,843 [INFO] Description: vocera-edge-server-4.x-oracle-8.6-08
2022-09-12 10:17:09,843 [INFO] CreationDate: 2022-08-08T17:04:10.000Z
2022-09-12 10:17:09,843 [INFO] State: available
2022-09-12 10:17:09,844 [INFO] Architecture: x86_64
2022-09-12 10:17:09,844 [INFO] ImageType: machine
2022-09-12 10:17:09,844 [INFO] Hypervisor: xen
2022-09-12 10:17:09,844 [INFO] RootDeviceType: ebs
2022-09-12 10:17:09,844 [INFO] VirtualizationType: hvm
2022-09-12 10:17:09,844 [INFO] Tags: [{'Key': 'Name', 'Value': 'vocera-edge-server-4.x-oracle-8.6-08'}]
2022-09-12 10:17:09,844 [INFO] ===================
2022-09-12 10:17:09,844 [INFO] Saving output in csv format
2022-09-12 10:17:09,844 [INFO] Creating /tmp/AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_091708-UTC.csv
2022-09-12 10:17:09,845 [INFO] File created successfully
2022-09-12 10:17:09,845 [INFO] File saved to /tmp/AMI-Report-vcra-nonprod-ap-south-1-2022-09-12_091708-UTC.csv
2022-09-12 10:17:09,845 [INFO] ===================
2022-09-12 10:17:09,845 [INFO] Found 9 AMI images
2022-09-12 10:17:09,845 [INFO] ===================
2022-09-12 10:17:09,845 [INFO] Script Complete
```
