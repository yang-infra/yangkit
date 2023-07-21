from setuptools import setup, find_packages

from yangkit.__version__ import __version__

setup(
    name='yangkit',
    version=__version__,
    description='Yang Kit Package',
    author='Jhansi',
    author_email='jhanm@cisco.com',
    url='https://github.com/yang-infra/yangkit',
    packages=find_packages()
)

