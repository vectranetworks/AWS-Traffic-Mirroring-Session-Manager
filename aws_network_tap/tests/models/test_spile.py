from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4
import boto3
from aws_network_tap.models.spile import Spile, ENI_Tag, Ec2ApiClient, MirrorSession


class TestSpile(TestCase):

    def mirror_session_factory(self, tags):
        return MirrorSession('catfood session', 'tmt-{}'.format(uuid4()), 'tmf-{}'.format(uuid4()), 'eni-{}'.format(uuid4()), tags)

    def test_should_manage_ours(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        mirror_session = self.mirror_session_factory({Spile.CREATOR_KEY: Spile.CREATOR_VALUE})
        self.assertTrue(spile.should_manage(mirror_session))

    def test_should_not_manage_others(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        mirror_session = self.mirror_session_factory({Spile.CREATOR_KEY: 'Bob Barker'})
        self.assertFalse(spile.should_manage(mirror_session))

    def test_should_not_manage_unknown(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        mirror_session = self.mirror_session_factory({})
        self.assertFalse(spile.should_manage(mirror_session))

    def test_manage_do_not_tap(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        spile._find_tap = MagicMock(return_value=None)
        result = spile.manage('arn:/foo/bar', do_tap=False)
        self.assertIsNone(result)

    def test_manage_do_tap(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        spile._find_tap = MagicMock(return_value=None)
        spile._tap = MagicMock()
        result = spile.manage('arn:/foo/bar', do_tap=True)
        self.assertIsNotNone(result)
        spile._tap.assert_called_once()

    def test_manage_not_running_prevents_tap(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_STOPPED)
        spile = Spile(boto3.client('s3'), eni_tag)
        spile._find_tap = MagicMock(return_value=None)
        result = spile.manage('arn:/foo/bar', do_tap=True)
        self.assertIsNone(result)

    def test_manage_no_change_already_tapped(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        existing_session = self.mirror_session_factory({Spile.CREATOR_KEY: Spile.CREATOR_VALUE})
        spile._find_tap = MagicMock(return_value=existing_session)
        result = spile.manage(existing_session.target_id, do_tap=True)
        self.assertEqual(existing_session, result)

    def test_manage_remove(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        existing_session = self.mirror_session_factory({Spile.CREATOR_KEY: Spile.CREATOR_VALUE})
        spile._find_tap = MagicMock(return_value=existing_session)
        spile._untap = MagicMock()
        result = spile.manage(existing_session.target_id, do_tap=False)
        self.assertIsNone(result)
        spile._untap.assert_called_once()

    def test_manage_change_target(self):
        eni_tag = ENI_Tag('id-12345', 'eth0', None, Ec2ApiClient.STATE_RUNNING)
        spile = Spile(boto3.client('s3'), eni_tag)
        existing_session = self.mirror_session_factory({Spile.CREATOR_KEY: Spile.CREATOR_VALUE})
        spile._find_tap = MagicMock(return_value=existing_session)
        spile._tap = MagicMock()
        result = spile.manage('tmt-12345', do_tap=True)
        self.assertIsNotNone(result)
        spile._tap.assert_called_once()