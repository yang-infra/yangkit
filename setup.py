from setuptools import setup, find_packages

from yangkit.__version__ import __version__

setup(
    name='yangkit',
    version=__version__,
    description='Yang Kit Package',
    author='Cafy',
    author_email='cafy-support@cisco.com',
    url='https://github.com/yang-infra/yangkit',
    packages=find_packages()
)
