#!/usr/bin/env python3
import os, sys, asyncio
import csv, json, yaml
import argparse
import logging
from datetime import datetime,timezone
import boto3
from botocore.exceptions import ClientError,ParamValidationError

# Global Variables
log_level=logging.INFO
log_format='%(asctime)s [%(levelname)s] %(message)s'
log_file="/dev/null"
date = datetime.now().strftime('%Y-%m-%d')
timestamp = datetime.now(timezone.utc).strftime('%H%M%S')

# Handle command line arguments
all_args = argparse.ArgumentParser(description='AWS EC2 AMI Reporting')
connection_group = all_args.add_argument_group('AWS Connection Details')
connection_group.add_argument('--aws-profile', '-a', required=False, default='default', help='AWS Profile: default = default', type=str)
connection_group.add_argument('--region', '-r', required=False, default='us-east-1',help="AWS Region: default = us-east-1 ", type=str)
instance_group = all_args.add_argument_group('Instance Details (Tags and/or Instance IDs)')
instance_group.add_argument('--product', '-p', required=False,help="EC2 Instance Product Tag", type=str)
instance_group.add_argument('--environment', '-e', required=False,help="EC2 Instance Environment Tag", type=str)
instance_group.add_argument('--tenant', '-t', required=False,help="EC2 Instance Tenant Tag", type=str)
instance_group.add_argument('--role', '-rl', required=False,help="EC2 Instance Role Tag", type=str)
instance_group.add_argument('--owner', '-o', required=False,help="EC2 Instance Owner Tag", type=str)
instance_group.add_argument('--name', '-n', required=False,help="EC2 Instance Name Tag", type=str)
instance_group.add_argument('--extra-tags', '-x', required=False, help='Other tags that can be used to search for AMI images as a comma separated key=value list (Example: -x key1=value1,key2=value2)', type=str)
instance_group.add_argument('--instance-ids', '-i', required=False, help='Instance IDs to create AMI from as a comma separated list', type=str)
log_group = all_args.add_argument_group('Log Options')
log_group.add_argument('--log-file', '-l', required=False, help='Log file location', type=str)
log_group.add_argument('--log-level', '-ll', required=False, default='INFO', help='Log level: default = INFO', type=str)
output_group = all_args.add_argument_group('Output Options')
output_group.add_argument('--no-save', '-ns', required=False, help='Do not save list of AMIs', action='store_true')
output_group.add_argument('--format', '-fm', required=False, default='csv', help='Output format. Accepted values: csv (default), json, yaml', type=str)
output_group.add_argument('--filename', '-f', required=False, help='File name for output: default = AMI-Report-<aws_profile>-<region>-<date>_<timestamp>.csv', type=str)
output_group.add_argument('--output-dir', '-d', required=False, help='Directory to store output files: default = current directory', type=str)
display_group = all_args.add_mutually_exclusive_group()
display_group.add_argument('--verbose', '-v', required=False, help='Verbose output', action='store_true')
display_group.add_argument('--silent', '-s', required=False, help='Do not display AMI details', action='store_true')
args=all_args.parse_args()

# Parse passed arguments and update logging variables if needed
for key, value in vars(args).items():
    if (key == 'log_file' and not value is None):
        log_file=value
    if key == 'log_level':
        log_level=value.upper()
    if key == 'format':
        if value is not None:
            args.format=value.lower()
        else:
            args.format='csv'
    if key == 'filename':
        if value is None:
            args.filename="AMI-Report-{}-{}-{}_{}-UTC".format(args.aws_profile,args.region,date,timestamp)
        # If filename is provided, remove file extension if provided
        if value is not None:
            args.filename=os.path.splitext(value)[0]
    if key == 'output_dir':
        if value is None:
        # Set default output file location if not passed as current directory
            args.output_dir = "./"
        if value is not None:
            # Strip trailing slash from output directory if provided
            args.output_dir = value.rstrip('/')

# Configure logging
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
    )

def main (): # Main function
    logging.info("===================")
    logging.info("AMI Image Report")
    logging.info("===================")
    print_args(args) # Print arguments passed from command line
    aws_connect(args) # Connect to AWS
    # Build a list of filters based on provided arguments
    filters = prepare_tags(args)
    # prepare_tags(args) # Prepare list of filter tags for use in AWS API call
    amis = find_amis(filters) # Find AMIs based on filter tags
    # If verbose output is enabled, print AMI details
    print_amis(amis) # Print AMIs found
    # If no-save is not enabled, save AMI details to file
    if not args.no_save:
        save_output(amis) # Save AMI details to file
    if not args.silent:
        logging.info("===================")
        logging.info("Found {0} AMI images".format(len(list(amis))))
        logging.info("===================")
        logging.info("Script Complete")

def print_args(args): # Print arguments passed from command line
    # If silent mode is enabled, do not print arguments
    if args.silent:
        logging.warning("Silent mode enabled. Minimal output only will be displayed.")
        return
    if args.no_save:
        args.filename = "None"
        args.output_dir = "None"
    logging.info("Supplied arguments")
    logging.info("===================")
    for key, value in vars(args).items():
        # Replace _ with space and capitalize first letter of each word
        key = key.replace("_"," ").title()
        logging.info('{0} : {1}'.format(key, value))
    if args.no_save:
        logging.warning("No Save Mode Enabled: AMI details will not be saved to file")
        logging.warning("No Save Mode Enabled: Filename and Output Directory have been set to None")
    logging.info("===================")

def aws_connect(args): # Connect to AWS
    try:
        global session
        
        if args.verbose:
            logging.info("Connecting to AWS")
        session = boto3.Session(profile_name=args.aws_profile,region_name=args.region)
        if not args.silent:
            logging.info("Connected to AWS")
        if args.verbose:
            logging.info("Session Details: {0}".format(session))
        if not args.silent:
            logging.info("===================")
    except ClientError as e:
        logging.error("Error in aws_connect: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in aws_connect: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def prepare_tags(args): # Prepare tags dictionary for use as filters in searching AMIs
    filters = []
    logging.debug("(prepare_tags) Preparing tags dictionary")
    for key, value in vars(args).items():
        logging.debug("(prepare_tags) {0} : {1}".format(key, value))
        if not (value is None or key == 'aws_profile' or key == 'region' or key == 'log_file' or key == 'log_level' or key == 'instance_ids' or key == 'extra_tags' or key == 'no_save' or key == 'format' or key == 'filename' or key == 'output_dir' or key == 'verbose' or key == 'silent' ): # Ignore None values and profile, region, logging, additional tags, or output details
            # Build search filters based on provided tag arguments
            json_data = {'Name': 'tag:' + key.capitalize(), 'Values': [value]}
            filters.append(json_data)
    # Handle extra-tags if supplied
    if args.extra_tags:
        if args.extra_tags is not None:
            extra_tags=args.extra_tags.split(',')
            for tag in extra_tags:
                key, value = tag.split('=')
                json_data = {'Name': 'tag:' + key.capitalize(), 'Values': [value]}
                filters.append(json_data)
    # If verbose output is enabled, print filters
    if args.verbose:
        logging.info("Filters: {0}".format(filters))
    return filters

def find_amis(filters): # Search for AMI images based on filters
    if not args.silent:
        logging.info("Searching for AMIs")
    try:
        ec2 = session.resource('ec2')
        amis = ec2.images.filter(Owners=['self'],Filters=filters)
        logging.debug("(find_amis) Found {0} AMI images".format(len(list(amis))))
        # Sort amis by creation date
        logging.debug("(find_amis) Sorting AMI images by creation date - oldest first")
        amis = sorted(amis, key=lambda x: x.creation_date, reverse=False) # Sorted oldest to newest
        return amis
    except ClientError as e:
        logging.error("Error in find_amis: {0}".format(e))
        sys.exit(1)
    except ParamValidationError as e:
        logging.error("Error in find_amis: {0}".format(e))
        sys.exit(1)
    except NameError as e:
        logging.error("Error in find_amis: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in find_amis: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def print_amis(amis): # Print AMI details
    # For each AMI found, print details imageId, name, description, creationDate, state, architecture, imageType, hypervisor, rootDeviceType, virtualizationType, tags to console
    try:
        if args.silent:
            return
        logging.info("===================")
        logging.info("Found {0} AMI images".format(len(list(amis))))
        # If silent is not enabled, but verbose is also not set print short AMI details
        if not args.verbose:
            logging.info("===================")
            for ami in amis:
                logging.info("ImageId: {0}, Name: {1}, Created Date: {2}".format(ami.image_id, ami.name, ami.creation_date))
        # If verbose output is enabled, print AMI details
        if args.verbose:
            logging.info("===================")
            for ami in amis:
                logging.info("ImageId: {0}".format(ami.id))
                logging.info("Name: {0}".format(ami.name))
                logging.info("Description: {0}".format(ami.description))
                logging.info("CreationDate: {0}".format(ami.creation_date))
                logging.info("State: {0}".format(ami.state))
                logging.info("Architecture: {0}".format(ami.architecture))
                logging.info("ImageType: {0}".format(ami.image_type))
                logging.info("Hypervisor: {0}".format(ami.hypervisor))
                logging.info("RootDeviceType: {0}".format(ami.root_device_type))
                logging.info("VirtualizationType: {0}".format(ami.virtualization_type))
                logging.info("Tags: {0}".format(ami.tags))
                logging.info("===================")
    except ClientError as e:
        logging.error("Error in find_amis: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in find_amis: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def save_output(amis): # Save AMI details to file
    try:
        #Validate file format is either csv, json, or yaml and default to csv if not
        logging.debug("(save_output) Validating file format")
        logging.debug("(save_output) File format: {0}".format(args.format))
        logging.debug("(save_output) File name: {0}".format(args.filename))
        if args.format == 'csv' or args.format == 'json' or args.format == 'yaml':
            if not args.silent:
                logging.info("Saving output in {0} format".format(args.format))
        else:
            logging.warning("Invalid output format specified")
            logging.warning("Valid formats are csv, json, or yaml")
            logging.warning("Defaulting to csv")
            args.format = 'csv'
        # Validate output directory exists and create if not
        logging.debug("(save_output) Validating output directory")
        dirExists = os.path.isdir(args.output_dir)
        if dirExists:
            logging.debug("(save_output) Output directory exists")
        else:
            os.makedirs(args.output_dir)
        # Valiate filename does not already exist and if it does, append a number to the end
        logging.debug("(save_output) Validating file exists")
        logging.debug("(save_output) Checking for {0}".format(args.output_dir + "/" + args.filename + "." + args.format))
        fileExists = os.path.isfile(args.output_dir + "/" + args.filename + "." + args.format)
        if fileExists:
            logging.debug("(save_output) File exists")
            i = 1
            # Test if the provided filename already exists in the directory and if so, append a number to the end, increment the number if the file still exists
            fileExists = os.path.isfile(args.output_dir + "/" + args.filename + "." + args.format)
            if fileExists == True:
                while fileExists == True:
                    logging.debug("(save_output) Append value: {0}".format(i))
                    i += 1
                    logging.debug("(save_output) Append value: {0}".format(i))
                    fileExists = os.path.isfile(args.output_dir + "/" + args.filename + "_" + str(i) + "." + args.format)
                args.filename = args.filename + "_" + str(i)
                logging.debug("(save_output) New filename: {0}.{1}".format(args.filename, args.format))
        # Finalising the filename including extension
        fullFilename = args.filename + "." + args.format
        if not args.silent:
            logging.info("Creating {0}/{1}".format(args.output_dir, fullFilename))
        if args.format == 'csv':
            logging.debug("(save_output) Creating csv file")
            # asyncio.run(save_csv(amis, fullFilename)) # Requires save_csv to be async
            save_csv(amis, fullFilename)
        if args.format == 'json':
            logging.debug("(save_output) Creating json file")
            logging.warning("JSON output not yet implemented")
            logging.warning("Defaulting to csv")
            fullFilename = args.filename + '.csv'
            save_csv(amis, fullFilename)
            # asyncio.run(save_json(amis, fullFilename)) # Requires save_json to be async
            # save_json(amis, fullFilename)
        if args.format == 'yaml':
            logging.debug("(save_output) Creating yaml file")
            logging.warning("YAML output not yet implemented")
            logging.warning("Defaulting to csv")
            fullFilename = args.filename + '.csv'
            save_csv(amis, fullFilename)
            # asyncio.run(save_yaml(amis, fullFilename)) # Requires save_yaml to be async
            # save_yaml(amis, fullFilename)
    except OSError as e:
        logging.error("Error in save_output: {0}".format(e))
        sys.exit(1)
    except TypeError as e:
        logging.error("Error in save_output: {0}".format(e))
        sys.exit(1)
    except UnboundLocalError as e:
        logging.error("Error in save_output: {0}".format(e))
        sys.exit(1)
    except:
        logging.error("Unexpected error in save_output: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def save_csv(amis, fullFileName): # Save AMI details to csv file
    try:
        logging.debug("(save_csv) Saving AMI details to csv file")
        # Create CSV file at args.output_dir/fullFileName
        # Write header row
        column_headers = ['ImageId', 'Name', 'Description', 'CreationDate', 'State', 'Architecture', 'ImageType', 'Hypervisor', 'RootDeviceType', 'VirtualizationType', 'Tags']
        with open(args.output_dir + "/" + fullFileName, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=column_headers)
            writer.writeheader()
            # Write data rows
            for ami in amis:
                writer.writerow({'ImageId': ami.id, 'Name': ami.name, 'Description': ami.description, 'CreationDate': ami.creation_date, 'State': ami.state, 'Architecture': ami.architecture, 'ImageType': ami.image_type, 'Hypervisor': ami.hypervisor, 'RootDeviceType': ami.root_device_type, 'VirtualizationType': ami.virtualization_type, 'Tags': ami.tags})
        # Check to see if file was created
        csvCreated = os.path.isfile(args.output_dir + "/" + fullFileName)
        if csvCreated:
            if not args.silent:
                logging.info("File created successfully")
            # Print path to file
            logging.info("File saved to {0}/{1}".format(args.output_dir, fullFileName))
    except OSError as e:
        logging.error("Error in save_csv: {0}".format(e))
    except TypeError as e:
        logging.error("Error in save_csv: {0}".format(e))
    except:
        logging.error("Unexpected error in save_csv: {0}".format(sys.exc_info()[0]))

# Note: issues serializing the boto3 ec2.Image object to json and yaml - both functions not implemented yet
# Note: amis is a list of ec2.Image class objects

def save_json(amis, fullFileName): # Save AMI details to json file
    try:
        logging.debug("(save_json) Saving AMI details to json file")
        # Create JSON file at args.output_dir/fullFileName
        # json_string = json.dumps(list(amis), default=lambda o: o.__dict__, sort_keys=True, indent=4)
        # logging.debug("(save_json) JSON string: {0}".format(json_string))
        with open(args.output_dir + "/" + fullFileName, 'w') as jsonfile:
            for ami in amis:
                # json.dump(ami._asdict(), jsonfile, default=lambda o: o.__dict__, sort_keys=True, indent=4)
                contents = ami['Body'].read().decode('utf-8')
                json.dump(contents, jsonfile, default=lambda o: o.__dict__, sort_keys=True, indent=4)
            # json.dump(list(amis), jsonfile)
        # Check to see if file was created
        jsonCreated = os.path.isfile(args.output_dir + "/" + fullFileName)
        if jsonCreated:
            if not args.silent:
                logging.info("File created successfully")
            # Print path to file
            logging.info("File saved to {0}/{1}".format(args.output_dir, fullFileName))
    except OSError as e:
        logging.error("Error in save_json: {0}".format(e))
    except TypeError as e:
        logging.error("Error in save_json: {0}".format(e))
    except AttributeError as e:
        logging.error("Error in save_json: {0}".format(e))
    except:
        logging.error("Unexpected error in save_json: {0}".format(sys.exc_info()[0]))

def save_yaml(amis, fullFileName): # Save AMI details to yaml file
    try:
        logging.debug("(save_yaml) Saving AMI details to yaml file")
        # Create YAML file at args.output_dir/fullFileName
        with open(args.output_dir + "/" + fullFileName, 'w') as yamlfile:
            for ami in amis:
                yaml.safe_dump(ami, yamlfile)
            # yaml.safe_dump(amis, yamlfile)
        # Check to see if file was created
        yamlCreated = os.path.isfile(args.output_dir + "/" + fullFileName)
        if yamlCreated:
            if not args.silent:
                logging.info("File created successfully")
            # Print path to file
            logging.info("File saved to {0}/{1}".format(args.output_dir, fullFileName))
    except OSError as e:
        logging.error("Error in save_yaml: {0}".format(e))
    except TypeError as e:
        logging.error("Error in save_yaml: {0}".format(e))
    except yaml.representer.RepresenterError as e:
        logging.error("Error in save_yaml: {0}".format(e))
    except:
        logging.error("Unexpected error in save_yaml: {0}".format(sys.exc_info()[0]))

main() # Call main function