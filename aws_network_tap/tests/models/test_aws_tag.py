from unittest import TestCase
from aws_network_tap.models.aws_tag import AWSTag


class TestAWSTag(TestCase):

    def test_to_dict(self):
        key = {
            'Key': 'Foo',
            'Value': 'Bar'
        }
        key_dict = AWSTag.to_dict([key])
        self.assertEqual({'Foo': 'Bar'}, key_dict)

    def test_to_dict_none(self):
        key_dict = AWSTag.to_dict([])
        self.assertEqual({}, key_dict)

    def test_to_tags(self):
        python_dict = {'Foo': 'Bar'}
        aws_tags = AWSTag.to_tags(python_dict)
        self.assertEqual([{
            'Key': 'Foo',
            'Value': 'Bar'
        }], aws_tags)

    def test_delete_tag(self):
        python_dict = {'Foo': AWSTag.Delete}
        self.assertEqual([{'Key': 'Foo'}], AWSTag.to_tags(python_dict))

    def test_delete_dict(self):
        tags = {'Key': 'Foo'}
        self.assertEqual({'Foo': AWSTag.Delete}, AWSTag.to_dict([tags]))