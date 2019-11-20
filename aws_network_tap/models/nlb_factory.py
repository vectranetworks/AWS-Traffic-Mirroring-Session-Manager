
from typing import Union, Set, List
import boto3  # type: ignore
from aws_network_tap.models.ec2_api_client import VENDOR, Ec2ApiClient


class NlbFactory:
    SPECIAL_NAME_SEED = VENDOR + "Tap"

    def __init__(self, region: str, vpc_id: str) -> None:
        self.region = region
        self.vpc_id = vpc_id
        self.client = boto3.client("elbv2", region_name=region)

    @property
    def lb_name(self) -> str:
        # 32 char limit
        return '{}{}'.format(self.SPECIAL_NAME_SEED, self.vpc_id.replace('vpc-', ''))[:32]

    def find_or_create(self) -> str:
        """ returns the ARN """
        arn = self.find_nlb()
        if arn:
            return arn
        return self.create_nlb()

    def find_nlb(self) -> Union[str, None]:
        try:
            response = self.client.describe_load_balancers(Names=[self.lb_name])["LoadBalancers"]
        except Exception as e:
            if "not found" not in str(e):
                raise
            return None
        if not response:
            return None
        if len(response) > 1:
            raise ValueError("invalid nlb count")
        return response[0]["LoadBalancerArn"]

    def create_nlb(self) -> str:
        seen_azs = set()  # type: Set[str]
        subnets = []  # type: List[str]
        for subnet in Ec2ApiClient(region=self.region, vpc_ids=[self.vpc_id]).list_subnets():
            if subnet.az not in seen_azs:
                seen_azs.add(subnet.az)
                subnets.append(subnet.subnet_id)
        response = self.client.create_load_balancer(
            Name=self.lb_name, Subnets=subnets, Scheme="internal", Type="network"
        )
        return response["LoadBalancers"][0]["LoadBalancerArn"]
