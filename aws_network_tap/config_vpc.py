"""
Used interactively to configure the VPCs that should be tapped.
No actual instance tapping happens until spile_driver is called
"""

import logging
from typing import Union
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, VPC_Props, Mirror_Target_Props
from aws_network_tap.models.nlb_factory import NlbFactory
from aws_network_tap.models.nlb_target_factory import NlbTargetFactory
from aws_network_tap.models.aws_tag import AWSTag


def find_target(region: str, vpc_id: str) -> str:
    make_nlb = 'y' in input("Create NLB (n) ? ").lower()
    if not make_nlb:
        raise ValueError('A target is required')
    target_arn = NlbFactory(region=region, vpc_id=vpc_id).find_or_create()
    logging.info("Created NLB")
    return target_arn


def find_mirror_target(region: str, vpc_id: str) -> Union[str, None]:
    """ return mirror target ARN """
    print("Choose a Mirror Target. Note: IP traffic must be routeable from the source ENI to the target.")
    for target in Ec2ApiClient.list_mirror_targets(region=region): # type: Mirror_Target_Props
        if target.vpc_bound and target.vpc_id != vpc_id:
            print(f'Warning: [{target.name}] is not recommended, unless transit gateway or vpc peering is in place.')
        if 'y' in input(f'Use Existing Session Mirror Target [{target.name}] {target.target_id}? (y) ').lower() or 'y':
            return target.target_id

    make_nlb_target = 'y' in input("Create New Session Mirroring Target? (n) ").lower()
    if not make_nlb_target:
        raise ValueError('A Mirror Target is required to continue')
    target_arn = find_target(region=region, vpc_id=vpc_id)
    d_target_id = NlbTargetFactory(region=region, vpc_ids=[vpc_id]).find_or_create(
        nlb_or_eni_arn=target_arn
    )
    logging.info("Created Session Mirroring Target")
    return d_target_id


def main() -> None:
    logging.getLogger().setLevel(logging.INFO)
    region = Ec2ApiClient.get_region()
    for vpc_prop in Ec2ApiClient.list_vpcs(region=region):  # type: VPC_Props
        current_tap_state = bool(vpc_prop.tags.get(Ec2ApiClient.TAG_KEY_VPC_TAP))
        desc = 'tapped' if current_tap_state else 'not tapped'
        change_config = 'y' in input(f'Change VPC {vpc_prop.name} ({vpc_prop.vpc_id} is currently {desc})? (n) ').lower()
        if not change_config:
            continue
        if current_tap_state:
            mirror_target_arn = AWSTag.Delete
        else:
            mirror_target_arn = find_mirror_target(region=region, vpc_id=vpc_prop.vpc_id)
        Ec2ApiClient.set_vpc_target(region=region, vpc_id=vpc_prop.vpc_id, session_mirror_target_arn=mirror_target_arn)
        logging.info('config updated')


if __name__ == '__main__':
    main()
