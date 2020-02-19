"""
Blacklists instances from being tapped.
Sensors and Brains should not be tapped.
"""

import logging
import os
from aws_network_tap.models.ec2_api_client import Ec2ApiClient
from aws_network_tap.models.tag_config import EC2Config


def set_blacklist(region: str, enabled: bool = True) -> None:
    mode = 'ADD TO' if enabled else 'REMOVE FROM'
    pasted_input = input(f"Enter instance_id (or comma separated list of instance_ids) {mode} blacklist: ")
    if not pasted_input:
        return
    instance_ids = [x.strip() for x in pasted_input.split(',')]
    if not instance_ids:
        return
    for instance_id in instance_ids:
        Ec2ApiClient.blacklist_instance(region=region, instance_id=instance_id, enabled=enabled)
    logging.info('Blacklists config updated')


def main() -> None:
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.getLogger().setLevel(log_level)
    region = Ec2ApiClient.get_region()
    set_blacklist(region=region, enabled=True)
    blacklist = Ec2ApiClient.get_instances_by_tag(region=region, tag=EC2Config.T_BLACKLIST)
    print(f"Current Blacklist: {blacklist}")
    set_blacklist(region=region, enabled=False)


if __name__ == '__main__':
    main()
