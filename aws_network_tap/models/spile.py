import logging
from typing import Union
import boto3  # type: ignore
from collections import namedtuple
from aws_network_tap.models.sap_filter import SapFilter
from aws_network_tap.models.ec2_api_client import ENI_Tag, VENDOR, Ec2ApiClient
from aws_network_tap.models.aws_tag import AWSTag

MirrorSession = namedtuple("SessionMirror", "id target_id filter_id interface_id tags")


class Spile:

    CREATOR_KEY = 'Creator'
    CREATOR_VALUE = VENDOR + ':Tap'

    def __init__(self, ec2_client: boto3.client, eni_tag: ENI_Tag):
        self.ec2_client = ec2_client
        self.eni_tag = eni_tag

    @property
    def session_number(self) -> int:
        return 1

    def _find_tap(self) -> Union[MirrorSession, None]:  # TODO paginate this one
        """ returns the traffic mirror session id"""

        try:
            response = self.ec2_client.describe_traffic_mirror_sessions(
                Filters=[
                    {
                        "Name": "network-interface-id",
                        "Values": [self.eni_tag.interface_id]
                    },
                    {
                        "Name": "session-number",
                        "Values": [str(self.session_number)],  # inconsistent!
                    },
                ]
            )["TrafficMirrorSessions"]
        except Exception as e:
            if "not found" not in str(e):
                raise
            return None
        if not response:
            return None
        if len(response) > 1:
            raise ValueError("too many filters installed")
        _ = response[0]
        return MirrorSession(
            _["TrafficMirrorSessionId"],
            _["TrafficMirrorTargetId"],
            _["TrafficMirrorFilterId"],
            _["NetworkInterfaceId"],
            AWSTag.to_dict(_["Tags"])
        )

    def _tap(self, target_id: str) -> Union[MirrorSession, None]:
        filter_id = SapFilter(ec2_client=self.ec2_client).install()
        # create session
        tags = {
            self.CREATOR_KEY: self.CREATOR_VALUE,
            AWSTag.NAME_KEY: self.eni_tag.tags.get(AWSTag.NAME_KEY, self.eni_tag.instance_id)}
        try:
            _ = self.ec2_client.create_traffic_mirror_session(
                NetworkInterfaceId=self.eni_tag.interface_id,
                TrafficMirrorTargetId=target_id,
                TrafficMirrorFilterId=filter_id,
                SessionNumber=self.session_number,
                Description="Vectra EC2 ".format(self.eni_tag.instance_id),
                TagSpecifications=[
                    {
                        'ResourceType': 'traffic-mirror-session',
                        'Tags': AWSTag.to_tags(tags)
                    }
                ],
            )["TrafficMirrorSession"]
        except Exception as e:
            if 'is in use by target' in str(e):
                logging.warning(f'unable to tap {self.eni_tag.instance_id} due to existing tap')
                return None
            if 'Sources per interface-target limit reached' in str(e):
                logging.warning(f'unable to tap {self.eni_tag.instance_id} due to target limit')
                return None
            raise

        return MirrorSession(
            _["TrafficMirrorSessionId"],
            _["TrafficMirrorTargetId"],
            _["TrafficMirrorFilterId"],
            _["NetworkInterfaceId"],
            AWSTag.to_dict(_["Tags"])
        )

    def _untap(self, mirror_session_id: str) -> None:
        self.ec2_client.delete_traffic_mirror_session(TrafficMirrorSessionId=mirror_session_id)

    def manage(self, target_id: str, do_tap: bool) -> Union[MirrorSession, None]:
        mirror_session = self._find_tap()
        if mirror_session:
            if not self.should_manage(mirror_session):
                logging.info(f'Ignoring externally managed session {mirror_session.id}')
                return None  # don't manage this one
            if self.eni_tag.state != Ec2ApiClient.STATE_RUNNING:
                self._untap(mirror_session.id)  # remove
                return None
            if do_tap:
                return mirror_session  # already tapped
            else:
                self._untap(mirror_session.id)
                return None
        else:
            if self.eni_tag.state != Ec2ApiClient.STATE_RUNNING:
                return None  # not running, no tap
            if do_tap:
                return self._tap(target_id)
            else:
                return None  # don't tap

    @classmethod
    def should_manage(cls, mirror_session: MirrorSession) -> bool:
        return mirror_session.tags.get(cls.CREATOR_KEY) == cls.CREATOR_VALUE
