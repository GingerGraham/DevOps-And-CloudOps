# Create And Tag EC2 AMIs

This is a version of the CreateAndTagEC2AMI python script updated specifically to work on AWS Lambda.  Due to the specific requirements for AWS Lambda some modifications were required to the original script.

This version delivers the same behaviour as the locally run version of the script.  AMI Images can be found in the AWS Console under EC2 --> Images --> AMIs.  Images will be created with the `Name` of the instance, and `AMI Name` of the instance tagged with the date and time the image was taken and with tags applied based on the tags attached to the instance along with the date and time the image was taken.

![AWS EC2 AMI Image with Tags](../assets/AWS-EC2-Images.png "AWS EC2 AMI Image with Tags")

## Function details

- Function URL: <https://7qyvxuugkjvkb26kwrvl4lrgh40ipzwd.lambda-url.us-east-1.on.aws/>
- Function Name: CreateAndTagEC2AMI

## Running the Lamdba function

AWS provides several ways to call a Lambda function.  When calling the function one or more [parameters](#parameters) should be passed with the function call.  Parameters can be passed inline or as a json object

### Using the AWS CLI

The Lambda function is called **`CreateAndTagEC2AMI`**.

More details on invoking a Lambda function from the AWS CLI can be found in the [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)

#### Inline Parameters for AWS CLI

The following command will call the function and pass the parameters inline in json syntax.  Note; an outfile such as `response.json` must be provided to capture the response from the function.

More details on invoking a Lambda function from the AWS CLI can be found in the [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)

The below example passes parameters for `product_tag=operations-tools` and `environment_tag=test`

```bash
aws lambda invoke --function-name CreateAndTagEC2AMIs --payload '{"product_tag": "operations-tools","environment_tag": "test"}' response.json
```

The above command will return the following response to the command line

```bash
ExecutedVersion: $LATEST
StatusCode: 200
(END)
```

The function returns a `null` return to `response.json`

#### JSON Parameters for AWS CLI

The `--payload` parameter can also consume a json file rather than inline json.

```bash
aws lambda invoke --function-name CreateAndTagEC2AMIs --payload ./params.json response.json
```

### Using a web request

Web requests can either be made from the command line using `curl` or from a web browser (when passing parameters inline).

#### Inline Parameters for a web request

When passing parameters inline the parameters should be passed in the url as a query string with multiple parameters separated by a `&` character.

The below example passes parameters for `product_tag=operations-tools` and `environment_tag=test`

```bash
curl -v -X POST 'https://7qyvxuugkjvkb26kwrvl4lrgh40ipzwd.lambda-url.us-east-1.on.aws/?product_tag=operations-tools&environment_tag=test'
```

The above request can also be made from a web browser by browsing to `https://7qyvxuugkjvkb26kwrvl4lrgh40ipzwd.lambda-url.us-east-1.on.aws/?product_tag=operations-tools&environment_tag=test`

#### JSON Parameters for a web request

Parameters can be supplied as a json object via `curl`

The below example passes parameters for `product_tag=operations-tools` and `environment_tag=test`

```bash
curl -v -X POST 'https://7qyvxuugkjvkb26kwrvl4lrgh40ipzwd.lambda-url.us-east-1.on.aws/' -d '{"product_tag": "operations-tools","environment_tag": "test"}'
```

## Parameters

The following limitations or requirements apply to the parameters:

**Note:** wildcards are not supported
**Note:** it is **not** recommended to set `wait` to `true` unless there is a specific requirement to have the Lambda function wait for the image to be created.  Setting this to `true` will cause the Lambda function to wait until the image is created before returning; this may take a long time and cause excessive charges for use of Lambda.

- `region`: Accepts a single region (e.g. `us-east-1` or `us-west-2`)
- `product_tag`: Accepts a single product tag (e.g. `product-1` or `product-2`)
- `environment_tag`: Accepts a single environment tag (e.g. `environment-1` or `environment-2`)
- `tenant_tag`: Accepts a single tenant tag (e.g. `tenant-1` or `tenant-2`)
- `role_tag`: Accepts a single role tag (e.g. `role-1` or `role-2`)
- `owner_tag`: Accepts a single owner tag (e.g. `me` or `you`)
- `name_tag`: Accepts a single name tag (e.g. `my-instance` or `your-instance`)
- `extra_tags`: Accepts a list of tags to further filter the instance list in the format `tag1=value1,tag2=value2` (e.g. `custom=test,name=my-instance`)
- `instance_id_list`: Accepts a comma separated list of instance IDs (e.g. `i-123456789,i-987654321`)
- `add_tags`: Accepts a comma separated list of tags to add to the AMI in the format `tag1=value1,tag2=value2` (e.g. `custom=test,name=my-instance`)
- `wait`: `true` or `false`.  The default value is `false`.  Setting this value to `true` will cause the script to wait for the AMI to be available before returning.

### Default Parameter Values

The following parameters have default values:

- `region`: `us-east-1`
- `wait`: `False`

### Parameter JSON Object

Below is an example JSON object including examples of all parameters and their values.

```json
{
  "region": "us-east-1",
  "product_tag": "product-1",
  "environment_tag": "environment-1",
  "tenant_tag": "tenant-1",
  "role_tag": "role-1",
  "owner_tag": "me",
  "name_tag": "my-instance",
  "extra_tags": "tag1=value1,tag2=value2",
  "instance_id_list": "i-123456789,i-987654321",
  "add_tags": "tag3=value3,tag4=value4",
  "wait": false
}
```

## Update the Lambda function

1. Ensure you have the latest version of the lambda function code pulled from the BitBucket repository
1. Open `scripts/CreateAndTagEC2AMI/Lambda/CreateAndTagEC2AMI.py` and copy the entire contents of the file
1. Navigate to the Lambda function in the AWS console <https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/CreateAndTagEC2AMIs?tab=code>
1. On the `Code` tab paste the contents of the Lambda function code into the `Code Source` section replacing the existing code
1. Click Deploy
1. Navigate to the `Versions` tab and click `Publish new version`
1. Optionally, set the `Description` and `Revision ID` fields
1. From the `Test` tab, click `Test` to test the Lambda function using one of the pre-saved tests or create your own test event if you need to test new functionality

## Differences between the Lambda function and the script

The following switch options from the script are not supported by the Lambda function:

- `--list-only`: This option to list the EC2 instances to be backed up without backing them up is not supported by the Lambda function as it is not easy to access the returned values from the Lambda function.  Be sure of your targets, or if you need this functionality use the script instead.
- `--log-file`: This option is not included as logging is handled directly in AWS CloudWatch Logs.
- `--log-level`: This option is not included as logging is handled directly in AWS CloudWatch Logs.
