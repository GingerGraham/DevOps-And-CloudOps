#!/bin/sh

# This script is used to query AWS for Lambda functions in each region, their ARN, runtime, last modified date, and last invocation date (if possible).

# This script requires the following applications to be installed:
REQUIRED_APPS=(aws date jq yq)
# Fields to query for from the Lambda functions
REQUIRED_FIELDS=(FunctionName FunctionArn Runtime LastModified)
# Max items to be queried per region
MAX_ITEMS=1000

# Function to call to get the current date and time - used for logging output primarily
function dateTime {
    date +"%Y-%m-%d %H:%M:%S"
}

# Function to 
function fileDateTime {
    date +"%Y-%m-%d_%H%M%S"
}

echo "$(dateTime) [INFO] Starting script"
echo "$(dateTime) [INFO] Checking for required applications"

# Confirm that the required applications are installed
for APP in "${REQUIRED_APPS[@]}"; do
    if ! command -v $APP &> /dev/null; then
        echo "$(dateTime) [ERROR] ${APP} could not be found"
        echo "$(dateTime) [WARN] Please install ${APP} and try again"
        exit 1
    fi
done

echo "$(dateTime) [INFO] Required applications found"

# Verify if the AWS Credentials are available
if [[ -f ~/.aws/credentials ]]; then
    echo "$(dateTime) [INFO] AWS Credentials found"
    AWS_CREDENTIALS=true
fi

# If AWS_CREDENTIALS is true, then check for default profile
if [[ ${AWS_CREDENTIALS} == true ]]; then
    if [ -z "$(grep -E '\[default\]' ~/.aws/credentials)" ]; then
        echo "$(dateTime) [WARN] No default profile found in ~/.aws/credentials"
    else
        DEFAULT_PROFILE="default"
    fi
fi

# Test if AWS CLI has a default profile set in environment variables under AWS_PROFILE or AWS_DEFAULT_PROFILE by testing if variable are not empty
# Set DEFAULT_PROFILE to the value of the variable
if [[ ! -z "${AWS_PROFILE}" ]]; then
    DEFAULT_PROFILE="${AWS_PROFILE}"
elif [[ ! -z "${AWS_DEFAULT_PROFILE}" ]]; then
    DEFAULT_PROFILE="${AWS_DEFAULT_PROFILE}"
fi

# Show the user the available profiles and ask if they want to use a profile
if [[ ${AWS_CREDENTIALS} == true ]]; then
    echo "$(dateTime) [INFO] AWS profiles found"
    echo "$(dateTime) [INFO] Available profiles:"
    echo "-------------------------"
    grep -E '\[.*\]' ~/.aws/credentials | sed 's/\[//g' | sed 's/\]//g'
    echo "-------------------------"
    read -p "$(dateTime) [INFO] Do you want to use a profile (default: no)? (y/n): " -r
    if [[ $REPLY =~ ^([yY][eE][sS]|[yY])$ ]]; then
        USE_PROFILE=true
    fi
fi

# If USE_PROFILE is true, then ask the user which profile to use, offer DEFAULT_PROFILE as the default option
if [[ ${USE_PROFILE} == true ]]; then
    read -p "$(dateTime) [INFO] Which profile do you want to use? (default: ${DEFAULT_PROFILE}): "  PROFILE
    if [[ -z ${PROFILE} ]]; then
        PROFILE=${DEFAULT_PROFILE}
    fi
fi

# Confirm back the profile that will be used
if [[ ${USE_PROFILE} == true ]]; then
    echo "$(dateTime) [INFO] Using profile: ${PROFILE}"
fi

# If not using a profile see if environment variables are set for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
if [[ ${USE_PROFILE} != true ]]; then
    if [[ ! -z "${AWS_ACCESS_KEY_ID}" ]] && [[ ! -z "${AWS_SECRET_ACCESS_KEY}" ]]; then
        USE_ENV_VARS=true
        ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
        SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    fi
fi

# If USE_ENV_VARS is true, then ask the user if they want to use the environment variables
if [[ ${USE_ENV_VARS} == true ]]; then
    echo "$(dateTime) [INFO] AWS_ACCESS_KEY_ID ${ACCESS_KEY_ID} and AWS_SECRET_ACCESS_KEY environment variables are set"
    read -p "$(dateTime) [INFO] Do you want to use the environment variables (default: no)? (y/n): " -r
    if [[ ! $REPLY =~ ^([yY][eE][sS]|[yY])$ ]]; then
        USE_ENV_VARS=false
    fi
fi

# If not using a profile or environment vars gather connection information
if [[ ${USE_PROFILE} != true ]] && [[ ${USE_ENV_VARS} != true ]]; then
    echo "Please enter the AWS Access Key ID"
    read -p "Access Key ID: " ACCESS_KEY_ID
    echo "Please enter the AWS Secret Access Key"
    read -s -p "Secret Access Key: " SECRET_ACCESS_KEY
    echo
fi

# Test AWS connection
if [[ -z "${PROFILE}" ]]; then
    echo "$(dateTime) [INFO] Testing AWS connection using Access Key ID ${ACCESS_KEY_ID}"
    CONNECT_SUCCESS=`aws sts get-caller-identity --query Arn --output text --region us-east-1 --aws-access-key-id ${ACCESS_KEY_ID} --aws-secret-access-key ${SECRET_ACCESS_KEY} --cli-connect-timeout 5 --cli-read-timeout 5`
else
    echo "$(dateTime) [INFO] Testing AWS connection using profile ${PROFILE}"
    CONNECT_SUCCESS=`aws sts get-caller-identity --query Arn --output text --region us-east-1 --profile ${PROFILE} --cli-connect-timeout 5 --cli-read-timeout 5`
fi

# If CONNECT_SUCCESS does not match the pattern `arn:aws:iam::[0-9]{12}:user/*` then the connection failed
if [[ ! ${CONNECT_SUCCESS} =~ arn:aws:iam::[0-9]{12}:user/* ]]; then
    echo "$(dateTime) [ERROR] AWS connection failed"
    echo "$(dateTime) [ERROR] Please check your connection information and try again"
    exit 1
fi

echo "$(dateTime) [INFO] AWS connection successful"

# If the all_regions.yml exists and is not empty, then pre-populate the REGIONS variable with the contents of the file
if [[ -s all_regions.yml ]]; then
    # echo "$(dateTime) [DEBUG] all_regions.yml found"
    REGIONS=($(yq eval '.regions[]' all_regions.yml | sort))
fi

# If REGIONS is not empty then print all available regions from REGIONS array
if [[ ! -z "${REGIONS}" ]]; then
    echo "$(dateTime) [INFO] Available regions"
    echo "-------------------------"
    for REGION in "${REGIONS[@]}"; do
        echo ${REGION}
    done
    echo "-------------------------"
    # Confirm if the user wants to query all regions, or provide a list of regions to query
    read -p "Do you want to query all regions (default: no) ? (y/n): " ALL_REGIONS
fi

if [[ $ALL_REGIONS =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "$(dateTime) [INFO] Querying all regions"
    QUERY_REGIONS=("${REGIONS[@]}")
else
    read -p "Please provide a list of regions to query (comma separated, default:us-east-1): " INPUT_REGIONS
fi

# Verify that the INPUT_REGIONS are valid regions against the REGIONS array if both arrays exists and reprompt for input if invalid
if [[ ! -z "${INPUT_REGIONS}" ]] && [[ ! -z "${REGIONS}" ]]; then
    # echo "$(dateTime) [DEBUG] INPUT_REGIONS: ${INPUT_REGIONS}"
    # echo "$(dateTime) [DEBUG] REGIONS: ${REGIONS[@]}"
    for REGION in $(echo ${INPUT_REGIONS} | sed "s/,/ /g"); do
        # echo "$(dateTime) [DEBUG] REGION: ${REGION}"
        if [[ ! " ${REGIONS[@]} " =~ " ${REGION} " ]]; then
            echo "$(dateTime) [ERROR] ${REGION} is not a valid region"
            # remove the invalid region from the INPUT_REGIONS comma separated list
            INPUT_REGIONS=$(echo ${INPUT_REGIONS} | sed -r "s/${REGION},{0,}//g")
        fi
    done
    # echo "$(dateTime) [DEBUG] INPUT_REGIONS: ${INPUT_REGIONS}"
    # If INPUT_REGIONS is empty after removing invalid regions, then update user and proceed with default region
    if [[ -z "${INPUT_REGIONS}" ]]; then
        echo "$(dateTime) [WARN] No valid regions provided, using default region: us-east-1"
    fi
fi


# If ALL_REGIONS is not true, and INPUT_REGIONS is empty, then set the default region to us-east-1
if [[ ! ${ALL_REGIONS} =~ ^([yY][eE][sS]|[yY])$ ]] && [[ -z "${INPUT_REGIONS}" ]]; then
    INPUT_REGIONS="us-east-1"
fi

# If INPUT_REGIONS is not empty, then set the QUERY_REGIONS array to the contents of INPUT_REGIONS
if [[ ! -z "${INPUT_REGIONS}" ]]; then
    QUERY_REGIONS=($(echo ${INPUT_REGIONS} | tr "," "\n"))
fi

echo "$(dateTime) [INFO] Querying the following regions:"
for REGION in "${QUERY_REGIONS[@]}"; do
    echo ${REGION}
done

# Create a directory for the output files based on the PROFILE or ACCESS_KEY_ID and the current date/time
if [[ -z "${PROFILE}" ]]; then
    OUTPUT_DIR="output/${ACCESS_KEY_ID}_$(fileDateTime)"
else
    OUTPUT_DIR="output/${PROFILE}_$(fileDateTime)"
fi
# Create the output directory
mkdir -p ${OUTPUT_DIR}

# Query AWS for Lambda functions in each region provided
if [[ -z "${PROFILE}" ]]; then
    echo "$(dateTime) [INFO] Querying AWS for Lambda functions using Access Key ID: ${ACCESS_KEY_ID}"
    for REGION in "${QUERY_REGIONS[@]}"; do
        echo "$(dateTime) [INFO] Querying ${REGION}"
        aws lambda list-functions --max-items ${MAX_ITEMS} --region ${REGION} --aws-access-key-id ${ACCESS_KEY_ID} --aws-secret-access-key ${SECRET_ACCESS_KEY} --output json > ${OUTPUT_DIR}/lambda_functions_${REGION}_$(fileDateTime).json
    done
else
    echo "$(dateTime) [INFO] Querying AWS for Lambda functions using profile: ${PROFILE}"
    for REGION in "${QUERY_REGIONS[@]}"; do
        echo "$(dateTime) [INFO] Querying ${REGION}"
        aws lambda list-functions --max-items ${MAX_ITEMS} --region ${REGION} --profile ${PROFILE} --output json > ${OUTPUT_DIR}/lambda_functions_${PROFILE}_${REGION}_$(fileDateTime).json
    done
fi

# If the json file is empty, then remove it
for FILE in $(find ${OUTPUT_DIR} -type f -name "*.json"); do
    if [[ ! -s ${FILE} ]]; then
        echo "$(dateTime) [WARN] ${FILE} is empty, removing file"
        rm ${FILE}
    fi
done

# Build a comma separated string of the values in the REQUIRED_FIELDS array
CSV_HEADER=$(IFS=, ; echo "${REQUIRED_FIELDS[*]}")
# echo "$(dateTime) [DEBUG] Required fields: ${CSV_HEADER}"

# Build a string of the values in the REQUIRED_FIELDS array with a comma between each value and where each value is prefixed with a period
# This is used to extract the values from the JSON file
JSON_SEARCH_STRING=$(IFS=, ; echo "${REQUIRED_FIELDS[*]/#/.}")
# echo "$(dateTime) [DEBUG] JSON search string: ${JSON_SEARCH_STRING}"

# If one or more files were created then continue
if [[ ! -z  $(find ${OUTPUT_DIR} -maxdepth 1 -name 'lambda_functions_*.json') ]]; then
    echo "$(dateTime) [INFO] Creating CSV file"
    # Build file name using fileDateTime function
    CSV_FILE_NAME="lambda_functions_${fileDateTime}.csv"
    # Create CSV file by echoing the CSV_HEADER string to the file
    echo ${CSV_HEADER} > ${OUTPUT_DIR}/${CSV_FILE_NAME}
    # Loop through all files created and append to CSV file
    for FILE in ${OUTPUT_DIR}/lambda_functions_*.json; do
        jq -r ".Functions[] | [${JSON_SEARCH_STRING}] | @csv" ${FILE} >> ${OUTPUT_DIR}/${CSV_FILE_NAME}
    done
    echo "$(dateTime) [INFO] CSV file created"
else
    echo "$(dateTime) [ERROR] No files were created"
    echo "$(dateTime) [ERROR] Please check your connection information and try again"
    exit 1
fi

# If PROFILE is not empty move csv file to file including profile name
if [[ ! -z "${PROFILE}" ]]; then
    mv ${OUTPUT_DIR}/${CSV_FILE_NAME} ${OUTPUT_DIR}/${PROFILE}_${CSV_FILE_NAME}
    echo "$(dateTime) [INFO] CSV file created: ${OUTPUT_DIR}/${PROFILE}_${CSV_FILE_NAME}"
else
    echo "$(dateTime) [INFO] CSV file created: ${OUTPUT_DIR}/${CSV_FILE_NAME}"
fi

echo "$(dateTime) [INFO] Script complete"