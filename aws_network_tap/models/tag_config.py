"""
These are models to hold business logic when using AWS Tags for persisted state,
and to assist serializing back to AWS's tag format after transformations.
"""

from typing import Union, List

from aws_network_tap.models.aws_tag import AWSTag
from aws_network_tap.constants import VENDOR


class TagConfig:
    """
    This is the abstract class. There are no tags keys defined, so it cannot hold any values.
    """
    TAGS = []  # override this list in each class with the keys used for a particular asset type

    def __init__(self, tags: dict = None) -> None:
        self.tags = tags if tags else {}

    def get_aws_tags(self) -> List[dict]:
        """
        return only the tags that are defined as part of a model config, and have been explicitly set, in AWS tag format
        """
        return AWSTag.to_tags({i: self.tags[i] for i in self.tags if i in self.TAGS})


class VPCTagConfig(TagConfig):
    """
    Holds VPC Level Configuration
    """
    T_TARGET = VENDOR + ':session_mirroring_target'  # arn
    T_ENROLLMENT = VENDOR + ':session_mirroring_enrollment'  # enum (Auto)

    TAGS = [
        T_TARGET,
        T_ENROLLMENT,
    ]

    @property
    def enabled(self) -> bool:
        return bool(self.target)

    @property
    def target(self) -> Union[str, None]:
        return self.tags[self.T_TARGET] if self.tags.get(self.T_TARGET) else None

    @target.setter
    def target(self, value: Union[str, None]) -> None:
        self.tags[self.T_TARGET] = value if value else AWSTag.Delete

    V_ENROLLMENT_AUTO = 'auto'
    V_ENROLLMENT_WHITELIST = 'whitelist'

    @property
    def enrollment(self) -> str:
        return self.tags.get(self.T_ENROLLMENT, self.V_ENROLLMENT_AUTO)

    @enrollment.setter
    def enrollment(self, value) -> None:
        if value not in [self.V_ENROLLMENT_AUTO, self.V_ENROLLMENT_WHITELIST, AWSTag.Delete]:
            raise ValueError('illegal option')
        self.tags[self.T_ENROLLMENT] = value

    @property
    def auto_enrollment(self) -> bool:
        return self.enrollment == self.V_ENROLLMENT_AUTO


class EC2Config(TagConfig):
    """
    Holds EC2 Level Configuration
    """
    T_BLACKLIST = VENDOR + ':session_mirroring_blacklist'
    T_WHITELIST = VENDOR + ':session_mirroring_whitelist'

    TAGS = [
        T_BLACKLIST,
        T_WHITELIST,
    ]

    V_TRUE = 'True'
    V_FALSE = AWSTag.Delete

    @property
    def blacklist(self) -> Union[bool, None]:
        if self.tags.get(self.T_BLACKLIST, 'shadow') == 'shadow':
            return None
        return self.tags.get(self.T_BLACKLIST) == self.V_TRUE

    @blacklist.setter
    def blacklist(self, value: bool) -> None:
        if value and self.whitelist:
            raise ValueError('cannot blacklist an instance which is whitelisted')
        self.tags[self.T_BLACKLIST] = self.V_TRUE if value else self.V_FALSE

    @property
    def whitelist(self) -> Union[bool, None]:
        if self.tags.get(self.T_WHITELIST, 'shadow') == 'shadow':
            return None
        return self.tags.get(self.T_WHITELIST) == self.V_TRUE

    @whitelist.setter
    def whitelist(self, value: bool) -> None:
        if value and self.blacklist:
            raise ValueError('cannot whitelist an instance which is blacklisted')
        self.tags[self.T_WHITELIST] = self.V_TRUE if value else self.V_FALSE
