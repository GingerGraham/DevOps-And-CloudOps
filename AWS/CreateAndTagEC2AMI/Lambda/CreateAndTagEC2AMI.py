import sys
import logging
import time
import concurrent.futures
import boto3
from botocore.exceptions import ClientError,ParamValidationError
from datetime import datetime

# Global Variables
log_level=logging.DEBUG
log_format='[%(levelname)s] %(asctime)s %(message)s'
instance_ids=[]
instance_amis={}
region = None
product_tag = None
environment_tag = None
tenant_tag = None
role_tag = None
owner_tag = None
name_tag = None
extra_tags = None
add_tags = None
instance_id_list= None
wait = None
date = datetime.now().strftime('%Y-%m-%d')
timestamp = datetime.now().strftime('%H:%M')

# Configure logging
logging.basicConfig(
    level=log_level,
    format=log_format
    )

def lambda_handler(event, context): # Main function
    # Capturing variables values from request
    region = event.get('region')
    product_tag = event.get('product_tag')
    environment_tag = event.get('environment_tag')
    tenant_tag = event.get('tenant_tag')
    role_tag = event.get('role_tag')
    owner_tag = event.get('owner_tag')
    name_tag = event.get('name_tag')
    extra_tags = event.get('extra_tags')
    add_tags = event.get('add_tags')
    instance_id_list = event.get('instance_id_list')
    wait = event.get('wait')
    # Setting default values for variables that need them if none are provided
    if region is None:
        region = 'us-east-1' # Default region
    if wait is None:
        wait = False # Default do not wait
    # Setting current date and time
    date = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%H:%M')
    print_args(region=region,product=product_tag,environment=environment_tag,tenant=tenant_tag,role=role_tag,owner=owner_tag,name=name_tag,instance_id_list=instance_id_list,wait=wait) # Print arguments passed from command line
    find_instances(region=region,product=product_tag,environment=environment_tag,tenant=tenant_tag,role=role_tag,owner=owner_tag,name=name_tag,instance_id_list=instance_id_list,extra_tags=extra_tags,wait=wait) # Find instances based on supplied arguments
    # If 1 or more instances are found iterate through all instances found and create AMI with tags
    if len(instance_ids) > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_ids)) as executor:
            for instance in instance_ids:
                executor.submit(create_and_tag_ami, instance, add_tags=add_tags)
            logging.info("===================")
        logging.info("Created AMIs")
        logging.info("===================")
        for key, value in instance_amis.items():
            logging.info("Image Name: {0} - Image ID: {1}".format(key, value))
        logging.info("===================")
        if wait == True:
            logging.info("Checking AMI states.  Please be patient this may take a few minutes")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_amis)) as executor:
                for key, value in instance_amis.items():
                    executor.submit(check_ami_state,value)
            logging.info("===================")
        logging.info("Confirming Successful AMI Image IDs")
        logging.info("===================")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(instance_amis)) as executor:
            for key, value in instance_amis.items():
                # logging.info("Image Name: {0} - Image ID: {1}".format(key, value))
                executor.submit(confirm_ami_success,key,value)
        logging.info("===================")
    else:
        logging.info("===================")
        logging.info("No instances found!")
        logging.info("===================")
    logging.info("All done!")
    sys.exit(0)

def create_and_tag_ami(instance, add_tags): # Create AMI and tag it
    tags=get_tags(instance, add_tags)
    image_id=create_ami(instance,tags)
    tag_ami(image_id,tags)

def print_args(**kwargs): # Print arguments passed from command line
    # kwargs=dict(kwargs)
    logging.info("Supplied arguments")
    logging.info("===================")
    for kw in kwargs:
        # Replace _ with space and capitalize first letter of each word
        key = kw.replace("_"," ").title()
        logging.info('{0} : {1}'.format(key,kwargs[kw]))
    logging.info("===================")

def find_instances(**kwargs): # Find instances based on supplied arguments
    try:
        logging.info("Finding instances based on tags")
        ec2 = boto3.client('ec2', region_name=region)
        filters = []
        for kw in kwargs:
            logging.debug("{0} : {1}".format(kw,kwargs[kw]))
            if not (kwargs[kw] is None or kw == 'aws_profile' or kw == 'region' or kw == 'log_file' or kw == 'log_level' or kw == 'wait' or kw == 'instance_id_list' or kw == 'extra_tags'): # Ignore None values and profile, region and logging details
                json_data = dict(Name = 'tag:' + kw.capitalize(), Values = [kwargs[kw]])
                filters.append(json_data)
        # Handle extra tags list if provided
        # Extra tags expected in a comma separated list of key=value pairs
        for kw in kwargs:
            if kw == 'extra_tags':
                extra_tags = kwargs[kw].split(',')
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
        for kw in kwargs:
            if kw == 'instance_id_list':
                if kwargs[kw] is not None:
                    for instance in kwargs[kw].split(','):
                        if instance not in instance_ids:
                            instance_ids.append(instance)
                            logging.info("Added instance ID: {0}".format(instance))
                        else:
                            logging.info("Instance ID: {0} already in list".format(instance))
            logging.info("All instances: {0}".format(instance_ids))
    except ClientError as e:
        logging.error("Error in find_instances: {0}".format(e))
        logging.error("Arguments: {0}".format(kwargs))
        sys.exit(1)
    except ParamValidationError as param_error:
        logging.error("Error in find_instances: {0}" .format(param_error))
        logging.error("Arguments: {0}".format(kwargs))
        sys.exit(1) 
    except AttributeError as attr_error:
        logging.error("Error in find_instances: {0}" .format(attr_error))
        logging.error("Arguments: {0}".format(kwargs))
        sys.exit(1)
    except:
        logging.error("Unexpected error in find_instances! Arguments provided: {0}".format(kwargs))
        logging.error("Unexpected error in find_instances: {0}".format(sys.exc_info()[0]))
        sys.exit(1)

def get_tags(instance, add_tags): # Get tags for instances
    try:
        logging.info("Getting tags for instance {0}".format(instance))
        ec2 = boto3.resource('ec2', region_name=region)
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
         # If add_tags is not empty add the additional tags to the list of tags to be attached to the AMI
        if add_tags is not None:
            for tag in add_tags.split(','):
                key, value = tag.split('=')
                json_data = {'Key': key, 'Value': value}
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
        ec2 = boto3.client('ec2', region_name=region)
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
        ec2 = boto3.resource('ec2', region_name=region)
        image = ec2.Image(image_id)
        image.create_tags(Tags=tags)
        logging.info("Adding tags: {0}".format(tags))
        logging.info("Image {0} tagged".format(image_id))
    except ClientError as e:
        logging.error("Error in tag_ami: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in tag_ami: {0}".format(e))
        logging.error("Unexpected error in tag_ami: {0}".format(sys.exc_info()[0]))

def check_ami_state(image_id): # Check AMI state
    try:
        logging.info("Checking AMI state for {0} every 30 seconds".format(image_id))
        ec2 = boto3.client('ec2', region_name=region)
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
        ec2 = boto3.client('ec2', region_name=region)
        image_state = ec2.describe_images(ImageIds=[image_id])['Images'][0]['State']
        if image_state == 'available':
            logging.info("Image {0} (ID {1}) is available".format(image_name,image_id))
    except ClientError as e:
        logging.error("Error in confirm_ami_success: {0}".format(e))
    except Exception as e:
        logging.error("Unexpected error in confirm_ami_success: {0}".format(e))
        logging.error("Unexpected error in confirm_ami_success: {0}".format(sys.exc_info()[0]))
