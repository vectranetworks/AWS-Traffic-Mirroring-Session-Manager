"""
AWS Network Tapping Tool
For installing AWS Session Mirroring on Eligible Nitro instances.

Took takes a "tap everything" approach at the VPC level.
Specific instances can be opted out with the blacklist tool.

"""
import logging
from typing import List
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, VPC_Props
from aws_network_tap.models.spile_tapper import SpileTapper


def main() -> None:
    logging.getLogger().setLevel(logging.INFO)
    region = Ec2ApiClient.get_region()
    for vpc_prop in Ec2ApiClient.list_vpcs(region=region):  # type: VPC_Props
        logging.info(f" Managing Session Mirroring for VPC {vpc_prop.name}: {vpc_prop.vpc_id}")
        try:
            target_id = vpc_prop.tags[Ec2ApiClient.TAG_KEY_VPC_TAP]
        except KeyError:
            target_id = None
        blacklist = []  # type: List[str]
        SpileTapper.manage(region=region, vpc_ids=[vpc_prop.vpc_id], target_id=target_id, blacklist=blacklist)


if __name__ == "__main__":
    main()
