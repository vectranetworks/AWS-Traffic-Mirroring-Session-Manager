
from typing import Generator, List
from aws_network_tap.models.ec2_api_client import Ec2ApiClient, ENI_Tag
from aws_network_tap.models.spile import Spile
from aws_network_tap.models.aws_tag import AWSTag


class SpileTapper(Ec2ApiClient):

    FOREST_SPECIES = [
        # A1
        "a1.medium",
        "a1.large",
        "a1.xlarge",
        "a1.2xlarge",
        "a1.4xlarge",
        # C5
        "c5.large",
        "c5.xlarge",
        "c5.2xlarge",
        "c5.4xlarge",
        "c5.9xlarge",
        "c5.12xlarge",
        "c5.18xlarge",
        "c5.24xlarge",
        "c5.metal",
        # C5d
        "c5d.large",
        "c5d.xlarge",
        "c5d.2xlarge",
        "c5d.4xlarge",
        "c5d.9xlarge",
        "c5d.18xlarge",
        # C5n
        "c5n.large",
        "c5n.xlarge",
        "c5n.2xlarge",
        "c5n.4xlarge",
        "c5n.9xlarge",
        "c5n.18xlarge",
        "c5n.metal",
        # I3en
        "i3en.large",
        "i3en.xlarge",
        "i3en.2xlarge",
        "i3en.3xlarge",
        "i3en.6xlarge",
        "i3en.12xlarge",
        "i3en.24xlarge",
        "i3en.metal",
        # M5
        "m5.large",
        "m5.xlarge",
        "m5.2xlarge",
        "m5.4xlarge",
        "m5.8xlarge",
        "m5.12xlarge",
        "m5.16xlarge",
        "m5.24xlarge",
        "m5.metal",
        # M5a
        "m5a.large",
        "m5a.xlarge",
        "m5a.2xlarge",
        "m5a.4xlarge",
        "m5a.8xlarge",
        "m5a.12xlarge",
        "m5a.16xlarge",
        "m5a.24xlarge",
        # M5ad
        "m5ad.large",
        "m5ad.xlarge",
        "m5ad.2xlarge",
        "m5ad.4xlarge",
        "m5ad.12xlarge",
        "m5ad.24xlarge",
        # M5d
        "m5d.large",
        "m5d.xlarge",
        "m5d.2xlarge",
        "m5d.4xlarge",
        "m5d.8xlarge",
        "m5d.12xlarge",
        "m5d.16xlarge",
        "m5d.24xlarge",
        "m5d.metal",
        "p3dn.24xlarge",
        # R5
        "r5.large",
        "r5.xlarge",
        "r5.2xlarge",
        "r5.4xlarge",
        "r5.8xlarge",
        "r5.12xlarge",
        "r5.16xlarge",
        "r5.24xlarge",
        "r5.metal",
        # R5a
        "r5a.large",
        "r5a.xlarge",
        "r5a.2xlarge",
        "r5a.4xlarge",
        "r5a.8xlarge",
        "r5a.12xlarge",
        "r5a.16xlarge",
        "r5a.24xlarge",
        # R5ad
        "r5ad.large",
        "r5ad.xlarge",
        "r5ad.2xlarge",
        "r5ad.4xlarge",
        "r5ad.12xlarge",
        "r5ad.24xlarge",
        # R5d
        "r5d.large",
        "r5d.xlarge",
        "r5d.2xlarge",
        "r5d.4xlarge",
        "r5d.8xlarge",
        "r5d.12xlarge",
        "r5d.16xlarge",
        "r5d.24xlarge",
        "r5d.metal",
        # T3
        "t3.nano",
        "t3.micro",
        "t3.small",
        "t3.medium",
        "t3.large",
        "t3.xlarge",
        "t3.2xlarge",
        # T3a
        "t3a.nano",
        "t3a.micro",
        "t3a.small",
        "t3a.medium",
        "t3a.large",
        "t3a.xlarge",
        "t3a.2xlarge",
        # z1d
        "z1d.large",
        "z1d.xlarge",
        "z1d.2xlarge",
        "z1d.3xlarge",
        "z1d.6xlarge",
        "z1d.12xlarge",
        "z1d.metal",
    ]

    def discover(self) -> Generator[Spile, None, None]:
        """ find all the nitro instances and return a Spile if so"""
        paginator = self.ec2_client.get_paginator("describe_instances")
        filters = [{"Name": "instance-type", "Values": self.FOREST_SPECIES}]
        if self.vpc_ids:
            filters.append({"Name": "vpc-id", "Values": self.vpc_ids})
        page_iterator = paginator.paginate(Filters=filters)
        for page in page_iterator:
            for garbo in page["Reservations"]:
                for instance in garbo["Instances"]:
                    instance_id = instance["InstanceId"]
                    tags = AWSTag.to_dict(instance["Tags"])
                    for interface in instance["NetworkInterfaces"]:
                        yield Spile(
                            ec2_client=self.ec2_client,
                            eni_tag=ENI_Tag(
                                instance_id,
                                interface["NetworkInterfaceId"],
                                tags,
                                instance["State"]["Name"]
                            ),
                        )

    @classmethod
    def manage(cls, region: str, vpc_ids: List[str], target_id: str, blacklist: List[str] = None) -> None:
        tapper = SpileTapper(region=region, vpc_ids=vpc_ids)
        ec2_blacklist = Ec2ApiClient.get_blacklist(region=region)
        for spile in tapper.discover():  # type: Spile
            do_tap = bool(target_id)
            if blacklist and spile.eni_tag.instance_id in blacklist:
                do_tap = False
            if spile.eni_tag.instance_id in ec2_blacklist:
                do_tap = False
            spile.manage(target_id=target_id, do_tap=do_tap)
