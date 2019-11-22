"""
Used interactively to configure the VPCs that should be tapped.
No actual instance tapping happens until spile_driver is called
"""

import logging
from typing import Union
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, VPC_Props, Mirror_Target_Props
from aws_network_tap.models.nlb_factory import NlbFactory
from aws_network_tap.models.nlb_target_factory import NlbTargetFactory
from aws_network_tap.models.tag_config import VPCTagConfig


def find_target(region: str, vpc_id: str) -> str:
    make_nlb = 'y' in input("Create new Network Load Balancer (n) ? ").lower()
    if not make_nlb:
        raise ValueError('A target is required')
    target_arn = NlbFactory(region=region, vpc_id=vpc_id).find_or_create()
    logging.info(f"Created Network Load Balancer {target_arn}")
    return target_arn


def find_mirror_target(region: str, vpc_id: str) -> Union[str, None]:
    """ return mirror target ARN """
    print("Choose a Mirror Target. Note: IP traffic must be routable from the source ENI to the target.")

    for target in Ec2ApiClient.list_mirror_targets(region=region):  # type: Mirror_Target_Props
        if target.vpc_bound and target.vpc_id != vpc_id:
            print(f'Warning: [{target.name}] is not recommended, unless transit gateway or vpc peering is in place.')

        if 'y' in (input(f'Use existing Traffic Mirror Target [{target.name}] {target.target_id}? (n) ').lower() or 'n'):
            return target.target_id

    make_nlb_target = 'y' in input("Create new Traffic Mirroring Target? (n) ").lower()
    if not make_nlb_target:
        raise ValueError('A Mirror Target is required to continue')
    target_arn = find_target(region=region, vpc_id=vpc_id)
    d_target_id = NlbTargetFactory(region=region, vpc_ids=[vpc_id]).find_or_create(
        nlb_or_eni_arn=target_arn
    )
    logging.info(f"Created Traffic Mirroring Target {d_target_id}")
    return d_target_id


def prompt_vpc_config(vpc_prop: VPC_Props, region: str) -> None:
    """
    The VPC configuration is stored in the account using tags, per the properties supported in VPCTagConfig
    """
    current_config = VPCTagConfig(vpc_prop.tags)
    desc = 'enabled to `{}` with enrollment mode `{}`'.format(current_config.target, current_config.enrollment) if current_config.enabled else 'disabled'
    change_config = 'y' in input(f'Modify VPC config for {vpc_prop.vpc_id}:{vpc_prop.name} (currently {desc})? (n) ').lower()
    if not change_config:
        return
    if current_config.enabled and 'y' in input(f"Disable Traffic Mirroring for this VPC? (n) ").lower():
        mirror_target_arn = None
    else:
        mirror_target_arn = find_mirror_target(region=region, vpc_id=vpc_prop.vpc_id)
    new_config = VPCTagConfig(vpc_prop.tags)
    new_config.target = mirror_target_arn
    auto_mode_default = 'y' if current_config.auto_enrollment else ''
    resp = input(
        f"Enrollment Mode: "
        f"Y for {VPCTagConfig.V_ENROLLMENT_AUTO} mode, "
        f"N for {VPCTagConfig.V_ENROLLMENT_WHITELIST} mode. "
        f"(Currently {current_config.enrollment}) "
        f"Mirror all instances by default? ({auto_mode_default}) ").lower() or auto_mode_default
    auto_mode = 'y' in resp
    new_config.enrollment = VPCTagConfig.V_ENROLLMENT_AUTO if auto_mode else VPCTagConfig.V_ENROLLMENT_WHITELIST
    Ec2ApiClient.set_vpc_config(region=region, vpc_id=vpc_prop.vpc_id, config=new_config)
    logging.info(f'VPC Traffic Mirroring Target updated to {mirror_target_arn} in {new_config.enrollment} Enrollment Mode')


def main() -> None:
    logging.getLogger().setLevel(logging.INFO)
    region = Ec2ApiClient.get_region()
    for vpc_prop in Ec2ApiClient.list_vpcs(region=region):  # type: VPC_Props
        prompt_vpc_config(vpc_prop, region)


if __name__ == '__main__':
    main()
