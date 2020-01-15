from unittest import TestCase
from aws_network_tap.models.aws_tag import AWSTag
from aws_network_tap.models.tag_config import VPCTagConfig, EC2Config, TagConfig
import logging
logging.getLogger().setLevel(logging.INFO)


class TestTagConfig(TestCase):
    def test_get_tags_empty(self):
        c = TagConfig()
        self.assertEqual([], c.get_aws_tags())

    def test_tags_insert(self):
        c = TagConfig()
        c.TAGS.append('Foo')
        self.assertEqual([], c.get_aws_tags())

    def test_tag_is_set_after_init(self):
        c = TagConfig()
        c.TAGS.append('Foo')
        c.tags['Foo'] = 'Bar'
        self.assertEqual([{'Key': 'Foo', 'Value': 'Bar'}], c.get_aws_tags())

    def test_tag_is_set_after_none_init(self):
        c = TagConfig()
        c.TAGS.append('Foo')
        c.tags['Foo'] = AWSTag.Delete
        self.assertEqual([{'Key': 'Foo'}], c.get_aws_tags())


class TestVPCTags(TestCase):

    def test_empty_config(self):
        config = VPCTagConfig()
        self.assertEqual([], config.get_aws_tags())

    def test_none(self):
        config = VPCTagConfig()
        self.assertFalse(config.enabled)
        self.assertIsNone(config.target)

    def test_enable(self):
        config = VPCTagConfig()
        config.target = 'arn:foo/bar'
        self.assertTrue(config.enabled)
        self.assertEqual('arn:foo/bar', config.target)

    def test_disable(self):
        config = VPCTagConfig()
        config.target = None
        self.assertFalse(config.enabled)

    def test_get_aws_tags(self):
        config = VPCTagConfig()
        config.target = 'arn:foo/bar'
        self.assertEqual([{'Key': 'Vectra:session_mirroring_target', 'Value': 'arn:foo/bar'}], config.get_aws_tags())

    def test_dump_garbage_tags(self):
        config = VPCTagConfig({
            VPCTagConfig.T_TARGET: 'arn:aws:foo/bar',
            'flavor': 'development',
        })
        self.assertTrue(config.enabled)
        self.assertEqual(1, len(config.get_aws_tags()), config.get_aws_tags())

    def test_enrollment_value_error(self):
        config = VPCTagConfig()
        with self.assertRaises(ValueError) as e:
            config.enrollment = 'cheese'

    def test_enrollment_default(self):
        config = VPCTagConfig()
        self.assertEqual(config.V_ENROLLMENT_AUTO, config.enrollment)

    def test_enrollment_set(self):
        config = VPCTagConfig()
        config.enrollment = config.V_ENROLLMENT_WHITELIST
        self.assertEqual(config.V_ENROLLMENT_WHITELIST, config.enrollment)
        config.target = 'arn:aws:foo/bar'
        self.assertEqual(2, len(config.get_aws_tags()))
        for tag in config.get_aws_tags():
            self.assertEqual(2, len(tag))

    def test_enrollment_set_none(self):
        config = VPCTagConfig()
        config.enrollment = None
        config.target = None
        self.assertEqual(2, len(config.get_aws_tags()))
        for tag in config.get_aws_tags():
            self.assertEqual(1, len(tag))


class TestEc2Tags(TestCase):

    def test_defaults(self):
        config = EC2Config()
        self.assertIsNone(config.blacklist)
        self.assertIsNone(config.whitelist)
        self.assertEqual([], config.get_aws_tags())

    def test_set_blacklist(self):
        config = EC2Config()
        config.blacklist = True
        self.assertTrue(config.blacklist)
        self.assertEqual([{'Key': 'Vectra:session_mirroring_blacklist', 'Value': 'True'}], config.get_aws_tags())

    def test_set_whitelist(self):
        config = EC2Config()
        config.whitelist = True
        self.assertTrue(config.whitelist)
        self.assertEqual([{'Key': 'Vectra:session_mirroring_whitelist', 'Value': 'True'}], config.get_aws_tags())

    def test_unset_whitelist(self):
        config = EC2Config()
        config.whitelist = False
        self.assertFalse(config.whitelist)
        self.assertEqual([{'Key': 'Vectra:session_mirroring_whitelist'}], config.get_aws_tags())

    def test_cannot_set_both_true(self):
        config = EC2Config()
        config.blacklist = True
        with self.assertRaises(ValueError) as e:
            config.whitelist = True

