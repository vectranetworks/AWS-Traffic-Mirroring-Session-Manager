

from collections import namedtuple
import logging
from typing import Iterable, List, Union, Dict
import boto3  # type: ignore
from ec2_metadata import ec2_metadata  # type: ignore
from aws_network_tap.models.aws_tag import AWSTag
from aws_network_tap.models.tag_config import VPCTagConfig, EC2Config
from aws_network_tap.constants import VENDOR

ENI_Tag = namedtuple("ENI_Tag", "instance_id interface_id tags state")
VPC_Props = namedtuple("VPC_Props", "vpc_id name tags")
Subnet_Props = namedtuple("Subnet_Props", "subnet_id name arn az")
Mirror_Target_Props = namedtuple("Mirror_Target_Props", "target_id name type vpc_id vpc_bound")


class Ec2ApiClient:
    cache = {}  # type: Dict[str, boto3.client]

    STATE_RUNNING = "running"

    def __init__(self, account_number: str = None, region: str = None, vpc_ids: List[str] = None):
        if not account_number:
            who = boto3.client("sts").get_caller_identity()
            account_number = who["Account"]
        self.account_number = account_number
        if not region:
            region = self.get_region()
        self.region = region
        self.ec2_client = self._get_client(self.region)
        self.vpc_ids = vpc_ids

    @classmethod
    def __get_region_ec2(cls) -> Union[str, None]:
        try:
            return ec2_metadata.region
        except:
            return None

    @classmethod
    def __get_region_aws_config(cls) -> Union[str, None]:
        try:
            return boto3.Session().region_name
        except:
            return None

    @classmethod
    def get_region(cls) -> str:
        REGION_KEY = 'region'
        if not cls.cache.get(REGION_KEY):
            region = cls.__get_region_ec2()
            if not region:
                region = cls.__get_region_aws_config()
            if not region:
                raise RuntimeError('region not available')
            cls.cache[REGION_KEY] = region
        return cls.cache[REGION_KEY]

    @classmethod
    def _get_client(cls, region: str) -> boto3.client:
        return boto3.client("ec2", region_name=region)

    @classmethod
    def list_vpcs(cls, region: str) -> Iterable[VPC_Props]:
        vpcs = cls._get_client(region=region).describe_vpcs()
        for vpc in vpcs["Vpcs"]:
            tags = AWSTag.to_dict(vpc.get(AWSTag.TAGS_KEY))
            yield VPC_Props(vpc["VpcId"], tags.get(AWSTag.NAME_KEY), tags)

    def list_subnets(self) -> Iterable[Subnet_Props]:
        subnets = self.ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": self.vpc_ids}]
        )
        for subnet in subnets["Subnets"]:
            tags = AWSTag.to_dict(subnet.get(AWSTag.TAGS_KEY))
            yield Subnet_Props(
                subnet["SubnetId"], tags.get(AWSTag.NAME_KEY), subnet["SubnetArn"], subnet["AvailabilityZoneId"]
            )
    TARGET_NIC = "network-interface"
    TARGET_NLB = 'network-load-balancer'

    @classmethod
    def list_mirror_targets(cls, region: str) -> Iterable[Mirror_Target_Props]:
        response = cls._get_client(region=region).describe_traffic_mirror_targets()['TrafficMirrorTargets']
        for target in response:
            tags = AWSTag.to_dict(target.get(AWSTag.TAGS_KEY))
            # get the VPC_ID
            if target['Type'] == cls.TARGET_NIC:
                try:
                    vpc_id = cls._get_client(region=region).describe_network_interfaces(NetworkInterfaceIds=[
                            target['NetworkInterfaceId'],
                    ])["NetworkInterfaces"][0]["VpcId"]
                    vpc_bound = True
                except Exception as e:
                    if 'does not exist' in str(e):
                        id = target['TrafficMirrorTargetId']
                        logging.warning(f'Invalid Instance Session Mirroring Target `{id}`, delete manually.')
                        continue
            if target['Type'] == cls.TARGET_NLB:
                try:
                    lb = boto3.client('elbv2', region_name=region).describe_load_balancers(
                        LoadBalancerArns=[
                            target['NetworkLoadBalancerArn']
                        ],
                    )['LoadBalancers'][0]
                except Exception as e:
                    if 'or more load balancers not found' in str(e):
                        id = target['TrafficMirrorTargetId']
                        logging.warning(f'Invalid NLB Session Mirroring Target `{id}`, delete manually.')
                        continue
                    raise
                vpc_id = lb["VpcId"]
                vpc_bound = True if lb.get("Schema") == "internal" else False
            yield Mirror_Target_Props(
                target['TrafficMirrorTargetId'],
                tags.get(AWSTag.NAME_KEY),
                target['Type'],
                vpc_id,
                vpc_bound
            )

    @classmethod
    def set_vpc_config(cls, region: str, vpc_id: str, config: VPCTagConfig) -> None:
        """ enables/disables tapping the vpc"""
        client = cls._get_client(region=region)
        if config.enabled:
            client.create_tags(Tags=config.get_aws_tags(), Resources=[vpc_id])
        else:
            client.delete_tags(Tags=config.get_aws_tags(), Resources=[vpc_id])

    @classmethod
    def blacklist_instance(cls, region: str, instance_id: str, enabled: bool) -> None:
        """ enables/disables instances being blacklisted from tapping """
        client = cls._get_client(region=region)
        config = EC2Config()
        config.blacklist = enabled
        if config.blacklist:
            client.create_tags(Tags=config.get_aws_tags(), Resources=[instance_id])
        else:
            client.delete_tags(Tags=config.get_aws_tags(), Resources=[instance_id])

    @classmethod
    def whitelist_instance(cls, region: str, instance_id: str, enabled: bool) -> None:
        """ enables/disables instances being whitelisted to tapping """
        client = cls._get_client(region=region)
        config = EC2Config()
        config.whitelist = enabled
        if config.whitelist:
            client.create_tags(Tags=config.get_aws_tags(), Resources=[instance_id])
        else:
            client.delete_tags(Tags=config.get_aws_tags(), Resources=[instance_id])

    @classmethod
    def get_instances_by_tag(cls, region: str, tag: str) -> List[str]:
        """ Tag should be EC2Config.T_WHITELIST or T_BLACKLIST """
        # TODO paginate this
        if tag not in EC2Config.TAGS:
            raise ValueError('only specific tags are supported')
        response = cls._get_client(region=region).describe_tags(Filters=[
            {
                'Name': 'tag:' + tag,
                'Values': [
                    EC2Config.V_TRUE,
                ]
            },
        ])['Tags']
        return [x['ResourceId'] for x in response]
