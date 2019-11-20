# AWS Session Mirroring Tool

This tool automates the creation and maintenance AWS Session Mirrors (Network Taps) of Nitro based EC2 instances.

| Notice: Usage of this tool can lead to significant AWS charges from the network taps created or the NLB data transfer charges. No warranty or recourse are provided. |
| --- |

What this tool solves:

- Creating/removing session mirrors on EC2 instances.
- 'healing' session mirrors in response to instance lifecycle events (created/destryed), when this tool is scheduled to run under AWS Lambda.

The tool can selectively tap all VPCs in an account, as well as tap each ENI (Elastic Network Interface) interface on an EC2.



AWS Session Mirroring Architecture
![SessionMirror Architecture!](docs/AWS_SessionMirror_Architecture.png)


This configuration scripts (session_mirror_blacklist, session_mirror_config_vpc) do the following:

1. Denote VPCs that should be tapped using AWS Tags
1. Denote EC2s that should be blacklisted using AWS Tags
1. [Optional] Create an AWS NLB (network load balancer) to be the target of Session Mirroring Traffic 

The runtime script (session_mirror_tap) does the following:

1. Discover all Nitro instances in the VPC, and their respective ENI's 
1. Create Session Mirrororing Filters
1. Create Traffic Mirroring Session on the ENI using Filters


![Network Tapping Tool!](docs/AWS_Network_Tap.png)



## Getting Started

### Requirements
- Python 3.6+
- virtualenv
- [AWS Credentials with appropriate permissions](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) or install them with [AWS CLI](https://aws.amazon.com/cli/)

### Installing
1. Clone this repo
```console
git clone git@github.com:vectranetworks/AWS-Session-Mirroring-Tool.git
```        
        
3. Install the commands
```console
python setup.py install
```

### Configuring an AWS Account for Session Mirroring
Before Session Mirroring can take place, each VPC must have a target configured, 
and any instances that should not participate (Vectra Sensor/Brain) need to be blacklisted.
This is done by applying tags to the AWS Account.

1. Blacklist individual instances by instance id or comma separated list of instance ids:
```console
session_mirror_blacklist (Interactive)
```

2. Configure the VPCs should participate in Session Mirroring:
```console
session_mirror_config_vpc (Interactive)
```
    
### Install the Session Mirrors (Network Taps)
Once configuration is done, the last command can be run unattended, and any time there is a change of EC2s on the network.
This step adds the Session Mirrors and starts sending traffic to the targets.
```console
session_mirror_tap (Unattended)
```


## Development
1. Set up the Virtualenv
```console
./venv.sh
source .venv/bin/activate
```   
2. Set the blacklist to include the Cognito Brain and Sensor instance ids by editing aws_network_tap.spile_driver

3. Run the tapper
```console
cd ..
python -m aws_network_tap.spile_driver 
```
