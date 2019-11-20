from typing import Union
import boto3  # type: ignore
from .ec2_api_client import VENDOR
from aws_network_tap.models.aws_tag import AWSTag

class SapFilter:
    def __init__(self, ec2_client: boto3.client):
        self.ec2_client = ec2_client

    @property
    def _filter_name(self) -> str:
        return VENDOR + " Filter"

    @property
    def _filter_description(self) -> str:
        return VENDOR + " Full Traffic + DNS Filter"

    def install(self) -> str:
        """ returns the filter id"""
        filter_id = self._find_filter()
        if filter_id:
            return filter_id
        return self._create_filter()

    def _find_filter(self) -> Union[str, None]:
        """ return the filter id"""
        try:
            filters = self.ec2_client.describe_traffic_mirror_filters(
                Filters=[
                    {
                        "Name": "description",  # name/name isn't supported
                        "Values": [self._filter_description],
                    }
                ]
            )["TrafficMirrorFilters"]
        except Exception as e:
            if "not found" not in str(e):
                raise
            return None
        if not filters:
            return None
        if len(filters) > 1:
            raise ValueError("too many filters")
        return filters[0]["TrafficMirrorFilterId"]

    def _create_filter(self) -> str:
        # create filter and return the filter id
        filter_response = self.ec2_client.create_traffic_mirror_filter(
            Description=self._filter_description,
            TagSpecifications=[
                {
                    "ResourceType": "traffic-mirror-filter",
                    "Tags": AWSTag.to_tags({AWSTag.NAME_KEY: self._filter_name}),
                }
            ],
        )
        filter_id = filter_response["TrafficMirrorFilter"]["TrafficMirrorFilterId"]
        # tap dns
        self.ec2_client.modify_traffic_mirror_filter_network_services(
            TrafficMirrorFilterId=filter_id,
            AddNetworkServices=['amazon-dns'],
        )
        # create filter rules
        for direction in ["ingress", "egress"]:
            for rule, cidr in zip([100, 200], ["0.0.0.0/0", "::/0"]):
                self.ec2_client.create_traffic_mirror_filter_rule(
                    TrafficMirrorFilterId=filter_id,
                    TrafficDirection=direction,
                    RuleNumber=rule,
                    RuleAction="accept",
                    DestinationCidrBlock=cidr,
                    SourceCidrBlock=cidr,
                    Description=VENDOR + " " + direction + " rule",
                )
        return filter_id
