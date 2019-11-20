import os
from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    REQUIRED = f.readlines()

setup(
    name='aws_network_tap',
    version='1.0',
    description='Creates Traffic Mirroring sessions (network taps) for Nitro instances in AWS',
    author='Matt Land',
    author_email='mland@vectra.ai',
    license='proprietary',
    packages=['aws_network_tap', 'aws_network_tap.models'],
    entry_points={
        'console_scripts': [
            'session_mirror_tap = aws_network_tap.tap:main',
            'session_mirror_config_vpc = aws_network_tap.config_vpc:main',
            'session_mirror_blacklist = aws_network_tap.blacklist:main',
        ]
    },
    install_requires=REQUIRED,
)