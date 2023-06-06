#!/usr/bin/env bash

# List of inbound ports and subnets to add to security groups, this script will loop through to add each port and subnet combination to each security group
inboundSubnets=("10.248.0.0/22" "10.249.0.0/22" "10.250.0.0/22") # List of subnets to add to inbound rules space separated
inboundPorts=("22" "443" "3389") # List of ports to add to inbound rules space separated

# List of outbound ports and subnets to add to security groups, this script will loop through to add each port and subnet combination to each security group
outboundSubnets=() # List of subnets to add to outbound rules space separated
outboundPorts=() # List of ports to add to outbound rules space separated

function main {
  test-aws-cli
}

function test-aws-cli {
  if ! [[ -x "$(command -v aws)" ]]; then
    echo 'Error: AWS CLI is not installed.' >&2
    echo 'Please install AWS CLI and try again.' >&2
    exit 1
  else
    echo 'AWS CLI is installed, proceeding...'
  fi
}

main