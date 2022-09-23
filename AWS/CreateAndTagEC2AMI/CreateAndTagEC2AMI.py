#!/usr/bin/env python3
import sys
import argparse
import logging
import time
import concurrent.futures
import boto3
from botocore.exceptions import ClientError,ParamValidationError
from datetime import datetime,timezone

# Global Variables
log_level=logging.INFO
log_format='%(asctime)s [%(levelname)s] %(message)s'
log_file="/dev/null"
date = datetime.now().strftime('%Y-%m-%d')
timestamp = datetime.now(timezone.utc).strftime('%H:%M')
instance_ids=[]
instance_amis={}

# Handle command line arguments
all_args = argparse.ArgumentParser(description='AWS EC2 AMI Creation and Tagging')
connection_group = all_args.add_argument_group('AWS Connection Details')
connection_group.add_argument('--aws-profile', '-a', required=False, default='default', help='AWS Profile: default = default (Example: -a vcra-prod)', type=str)
connection_group.add_argument('--region', '-r', required=False, default='us-east-1',help="AWS Region: default = us-east-1 (Example: -r us-east-2)", type=str)
instance_group = all_args.add_argument_group('Instance Details (Tags and/or Instance IDs)')
instance_group.add_argument('--product', '-p', required=False,help="EC2 Instance Product Tag (Example: -p holodeck)", type=str)
instance_group.add_argument('--environment', '-e', required=False,help="EC2 Instance Environment Tag (Example: -e sse)", type=str)
instance_group.add_argument('--tenant', '-t', required=False,help="EC2 Instance Tenant Tag (Example: -t gemini)", type=str)
instance_group.add_argument('--role', '-rl', required=False,help="EC2 Instance Role Tag (Example: -rl appliance)", type=str)
instance_group.add_argument('--owner', '-o', required=False,help="EC2 Instance Owner Tag (Example: -o gr_watts)", type=str)
instance_group.add_argument('--name', '-n', required=False,help="EC2 Instance Name Tag (Example: -n gw-al-test-01)", type=str)
instance_group.add_argument('--extra-tags', '-x', required=False, help='Other tags that can be used to search for AMI images as a comma separated key=value list (Example: -x key1=value1,key2=value2)', type=str)
instance_group.add_argument('--instance-ids', '-i', required=False, help='Instance IDs to create AMI from as a comma separated list (Example: -i id-123456,id-654321)', type=str)
instance_group.add_argument('--add-tags', '-at', required=False, help='Additional tags to add to AMI as a comma separated key=value list (Example: -at key1=value1,key2=value2)', type=str)
log_group = all_args.add_argument_group('Log Options')
log_group.add_argument('--log-file', '-l', required=False, help='Log file location (Example: -l /tmp/createAMI.log)', type=str)
log_group.add_argument('--log-level', '-ll', required=False, default='INFO', help='Log level: default = INFO (Example: -ll DEBUG)', type=str)
extra_group = all_args.add_mutually_exclusive_group()
extra_group.add_argument('--list-only', '-lo','--dry-run','--check','-C', required=False, action='store_true', help='[Flag] List instances that would be backed up to AMI and exit without creating AMI')
extra_group.add_argument('--wait', '-w', required=False, action='store_true', help='[Flag] Wait for AMI to be available')
args=all_args.parse_args()

# Parse passed arguments and update logging variables if needed
for key, value in vars(args).items():
    if (key == 'log_file' and not value is None):
        log_file=value
    if key == 'log_level':
        log_level=value.upper()

# Configure logging
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
    )

def main(): # Main function
    logging.info("===================")
    logging.info("Creating AMI Image(s) from EC2 Instance(s)")
    logging.info("===================")
    print_args(args) # Print arguments passed from command line
    aws_connect(args) # Connect to AWS
    find_instances(args) # Find instances based on supplied arguments
    # If 1 or more instances are found iterate through all instances found and create AMI with tags
    logging.info("===================")
    # Verify if list only flag is set, print instances and exit
    if args.list_only:
        if len(instance_ids) > 0:
            logging.info("List Only Flag Set")
            logging.info("Instances to be tagged")
            logging.info("===================")
            for instance in instance_ids:
                logging.info(instance)
            logging.info("===================")
            # Find and prints tags that would be attached to the AMI
            logging.info("Tags to be attached to AMI(s)")
            logging.info("===================")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_ids)) as executor:
                for instance in instance_ids:
                    executor.submit(get_tags,instance)
            logging.info("===================")
            logging.info("Exiting without creating AMI(s)")
        sys.exit(0)
    # If list only flag is not set, create AMI and tag
    if len(instance_ids) > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_ids)) as executor:
            for instance in instance_ids:
                executor.submit(create_and_tag_ami, instance)
        logging.info("===================")
        logging.info("Created AMIs")
        logging.info("===================")
        for key, value in instance_amis.items():
            logging.info("Image Name: {0} - Image ID: {1}".format(key, value))
        logging.info("===================")
        if args.wait:
            logging.info("Waiting for AMIs to be available")
            logging.info("===================")
            logging.info("Checking AMI states.  Please be patient this may take a few minutes")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_amis)) as executor:
                for key, value in instance_amis.items():
                    executor.submit(check_ami_state,value)
            logging.info("===================")
            logging.info("Confirming Successful AMI Image IDs")
            logging.info("===================")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_amis)) as executor:
            for key, value in instance_amis.items():
                logging.debug("Image Name: {0} - Image ID: {1}".format(key, value))
                executor.submit(confirm_ami_success,key,value)
        logging.info("===================")
    else:
        logging.info("===================")
        logging.info("No instances found!")
        logging.info("===================")
    logging.info("All done!")
    sys.exit(0)

def create_and_tag_ami(instance):
    tags=get_tags(instance)
    image_id=create_ami(instance,tags)
    tag_ami(image_id,tags)

def print_args(args): # Print arguments passed from command line
    logging.info("Supplied arguments")
    logging.info("===================")
    for key, value in vars(args).items():
        # Replace _ with space and capitalize first letter of each word
        key = key.replace("_"," ").title()
        logging.info('{0} : {1}'.format(key, value))
    logging.info("===================")

def aws_connect(args): # Connect to AWS
    try:
        global session
        logging.info("Connecting to AWS")
        session = boto3.Session(profile_name=args.aws_profile,region_name=args.region)
        logging.info("Connected to AWS")
        logging.info("Session Details: {0}".format(session))
        logging.info("===================")
    except ClientError as e:
        logging.error("Error in aws_connect: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in aws_connect: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def find_instances(args): # Find instances based on supplied arguments
    try:
        logging.info("Finding instances based on tags")
        ec2 = session.client('ec2')
        filters = []
        for key, value in vars(args).items():
            logging.debug("{0} : {1}".format(key, value))
            if not (value is None or key == 'aws_profile' or key == 'region' or key == 'log_file' or key == 'log_level' or key == 'list_only' or key == 'wait' or key == 'instance_ids' or key == 'extra_tags' or key == 'add_tags' ): # Ignore None values and profile, region, logging or additional tag details
                json_data = {'Name': 'tag:' + key.capitalize(), 'Values': [value]}
                filters.append(json_data)
        # Handle extra-tags dictionary if supplied
        # Extra tags expected in the format of key=value,key=value,key=value
        if args.extra_tags:
            if args.extra_tags is not None:
                extra_tags=args.extra_tags.split(',')
                for tag in extra_tags:
                    key, value = tag.split('=')
                    json_data = {'Name': 'tag:' + key.capitalize(), 'Values': [value]}
                    filters.append(json_data)
        logging.info("Filters: {0}".format(filters))
        if len(filters) > 0:
            reservations = ec2.describe_instances(Filters=filters)['Reservations']
            for reservation in reservations:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
            logging.info("Found instances: {0}".format(instance_ids))
        else:
            logging.info("No filters supplied.  Bypassing tag based instance search")
        # Add directly provided instance IDs to list checking first if they are not already in the list
        if args.instance_ids:
            if args.instance_ids is not None:
                logging.info("Direct instance IDs provided {0}".format(args.instance_ids))
                logging.info("Checking if they are not already in the list")
                for instance in args.instance_ids.split(','):
                    if instance not in instance_ids:
                        logging.info("Adding instance ID: {0}".format(instance))
                        instance_ids.append(instance)
                    else:
                        logging.info("Instance ID: {0} already in list".format(instance))
                logging.info("All instances: {0}".format(instance_ids))
    except ClientError as e:
        logging.error("Error in find_instances: {0}".format(e))
        logging.error("Arguments: {0}".format(args))
        sys.exit(1)
    except ParamValidationError as e:
        logging.error("Error in find_instances: {0}".format(e))
        logging.error("Arguments: {0}".format(args))
        sys.exit(1)
    except AttributeError as e:
        logging.error("Error in find_instances: {0}".format(e))
        logging.error("Arguments: {0}".format(args))
        sys.exit(1)
    except:
        logging.error("Unexpected error in find_instances: {0}".format(sys.exc_info()[0]))
        logging.error("Unexpected error in find_instances! Arguments provided: {0}".format(args))
        sys.exit(1)

def get_tags(instance): # Get tags for instances
    try:
        logging.info("Getting tags for instance {0}".format(instance))
        ec2 = session.resource('ec2')
        ec2instance=ec2.Instance(instance)
        logging.debug("Instance: {0}".format(ec2instance))
        logging.debug("Tags: {0}".format(ec2instance.tags))
        instance_tags = []
        for tag in ec2instance.tags:
            if (tag['Key'] == 'Name' or tag['Key'] == 'Product' or tag['Key'] == 'Environment' or tag['Key'] == 'Tenant' or tag['Key'] == 'Role'):
                json_data = {'Key': tag['Key'], 'Value': tag['Value']}
                instance_tags.append(json_data)
        # Adding a Date tag
        json_data = {'Key': 'Date', 'Value': date}
        instance_tags.append(json_data)
        # Adding a Time tag
        json_data = {'Key': 'Timestamp', 'Value': timestamp + ' UTC'}
        instance_tags.append(json_data)
        # If args.add_tags is not empty add the additional tags to the list of tags to be attached to the AMI
        if args.add_tags:
            if args.add_tags is not None:
                logging.debug("Additional tags provided: {0}".format(args.add_tags))
                add_tags=args.add_tags.split(',')
                logging.debug("Additional tags split: {0}".format(add_tags))
                for tag in add_tags:
                    key, value = tag.split('=')
                    logging.debug("Adding tag: {0} with value: {1}".format(key, value))
                    json_data = {'Key': key.capitalize(), 'Value': value}
                    logging.debug("Adding tag: {0}".format(json_data))
                    instance_tags.append(json_data)
        logging.info("Instance {1} tags: {0}".format(instance_tags, instance))
        return instance_tags
    except ClientError as e:
        logging.error("Error in get_tags: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in get_tags: {0}".format(e))
        logging.error("Unexpected error in get_tags: {0}".format(sys.exc_info()[0]))

def create_ami(instance,tags): # Create AMI
    try:
        logging.info("Creating AMI for instance {0}".format(instance))
        ec2 = session.client('ec2')
        for tag in tags:
            if tag['Key'] == 'Name':
                image_name = tag['Value'] + '-' + date + '-' + timestamp.replace(':', '')
                image_description = image_name
        response = ec2.create_image(InstanceId=instance, Name=image_name, Description=image_description, NoReboot=True)
        logging.debug("Service response for creating AMI: {0}".format(response))
        for field in response:
            if field == 'ImageId':
                image_id = response[field]
        logging.info("Image ID: {0}, Image Name: {1}, Image Description: {2}".format(image_id, image_name, image_description))
        instance_amis[image_name] = image_id
        return image_id
    except ClientError as e:
        logging.error("Error in create_ami: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in create_ami: {0}".format(e))
        logging.error("Unexpected error in create_ami: {0}".format(sys.exc_info()[0]))

def tag_ami(image_id, tags): # Tag AMI
    try:
        logging.info("Tagging AMI {0}".format(image_id))
        ec2 = session.resource('ec2')
        image = ec2.Image(image_id)
        image.create_tags(Tags=tags)
        logging.debug("Adding tags: {0}".format(tags))
        logging.info("Image {0} tagged".format(image_id))
    except ClientError as e:
        logging.error("Error in tag_ami: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in tag_ami: {0}".format(e))
        logging.error("Unexpected error in tag_ami: {0}".format(sys.exc_info()[0]))

def check_ami_state(image_id): # Check AMI state
    try:
        logging.info("Checking AMI state for {0} every 30 seconds".format(image_id))
        ec2 = session.client('ec2')
        image_state = ec2.describe_images(ImageIds=[image_id])['Images'][0]['State']
        logging.info("Image {1} state: {0}".format(image_state, image_id))
        while image_state == 'pending':
            time.sleep(30)
            image_state = ec2.describe_images(ImageIds=[image_id])['Images'][0]['State']
            logging.info("Image {1} state: {0}".format(image_state, image_id))
            if image_state != 'pending':
                if image_state == 'available':
                    logging.debug("Image {0} is available".format(image_id))
                    return True
                elif image_state == 'failed':
                    logging.error("Image {0} failed".format(image_id))
                    return False
                else:
                    logging.warning("Image {0} is in unknown state: {1} please verify manually from the AWS Console".format(image_id, image_state))
                    return False
    except ClientError as e:
        logging.error("Error in check_ami_state: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in check_ami_state: {0}".format(e))
        logging.error("Unexpected error in check_ami_state: {0}".format(sys.exc_info()[0]))

def confirm_ami_success(image_name,image_id): # Confirm AMI success
    try:
        ec2 = session.client('ec2')
        image_state = ec2.describe_images(ImageIds=[image_id])['Images'][0]['State']
        if image_state == 'available':
            logging.info("Image {0} (ID {1}) is available".format(image_name,image_id))
    except ClientError as e:
        logging.error("Error in confirm_ami_success: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in confirm_ami_success: {0}".format(e))
        logging.error("Unexpected error in confirm_ami_success: {0}".format(sys.exc_info()[0]))

main() # Call main function
