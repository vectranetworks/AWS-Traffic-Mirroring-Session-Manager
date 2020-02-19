"""
AWS Network Tapping Tool
For installing AWS Session Mirroring on Eligible Nitro instances.

Took takes a "tap everything" approach at the VPC level.
Specific instances can be opted out with the blacklist tool.

"""
import logging
import os
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, VPC_Props
from aws_network_tap.models.spile_tapper import SpileTapper
from aws_network_tap.models.tag_config import VPCTagConfig


def main() -> None:
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.getLogger().setLevel(log_level)
    region = Ec2ApiClient.get_region()
    for vpc_prop in Ec2ApiClient.list_vpcs(region=region):  # type: VPC_Props
        logging.info(f" Managing Session Mirroring for VPC {vpc_prop.name}: {vpc_prop.vpc_id}")
        config = VPCTagConfig(vpc_prop.tags)
        SpileTapper.manage(region=region, vpc_ids=[vpc_prop.vpc_id], config=config)


if __name__ == "__main__":
    main()
