"""
Blacklists instances from being tapped.
Sensors and Brains should not be tapped.
"""

import logging
from aws_network_tap.models.ec2_api_client import Ec2ApiClient


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
    region = Ec2ApiClient.get_region()
    set_blacklist(region=region, enabled=True)
    blacklist = Ec2ApiClient.get_blacklist(region=region)
    print(f"Current Blacklist: {blacklist}")
    set_blacklist(region=region, enabled=False)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()
