import logging
from typing import Union
from aws_network_tap.models.aws_tag import AWSTag
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, VENDOR


class NlbTargetFactory(Ec2ApiClient):
    def find_or_create(self, nlb_or_eni_arn: str) -> str:
        """ returns traffic mirror target id """
        target_id = self.find_target(nlb_or_eni_arn=nlb_or_eni_arn)
        if target_id:
            return target_id
        return self.create(nlb_or_eni_arn=nlb_or_eni_arn)

    def find_target(self, nlb_or_eni_arn: str) -> Union[str, None]:
        try:
            response = self.ec2_client.describe_traffic_mirror_targets(
                Filters=[{"Name": "network-load-balancer-arn", "Values": [nlb_or_eni_arn]}]
            )["TrafficMirrorTargets"]
        except Exception as e:
            if "not found" not in str(e):
                raise
            return None
        if not response:
            return None
        if len(response) > 1:
            raise ValueError("invalid target count")
        return response[0]["TrafficMirrorTargetId"]

    def create(self, nlb_or_eni_arn: str) -> str:
        # create the target (of the mirroring)
        kwargs = {
            "Description": VENDOR + "TrafficMirror",
            "TagSpecifications": [
                {
                    'ResourceType': 'traffic-mirror-target',
                    'Tags': AWSTag.to_tags({AWSTag.NAME_KEY: VENDOR + 'NLBTarget'})
                }
            ],
        }
        if "elasticloadbalancing" in nlb_or_eni_arn:
            kwargs["NetworkLoadBalancerArn"] = nlb_or_eni_arn
        else:
            kwargs["NetworkInterfaceId"] = nlb_or_eni_arn
        response = self.ec2_client.create_traffic_mirror_target(**kwargs)
        return response["TrafficMirrorTarget"]["TrafficMirrorTargetId"]
