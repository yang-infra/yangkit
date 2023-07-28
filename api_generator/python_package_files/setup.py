"""
Setup for yangkit model bundle
$PACKAGE$
"""

from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

INSTALL_REQUIREMENTS = ['yangkit==$CORE_VERSION$']

NMSP_PKG_NAME = "$PACKAGE$"
NMSP_PKG_VERSION = "$VERSION$"
NMSP_PKG_DEPENDENCIES = ['$DEPENDENCY$']

if len(NMSP_PKG_DEPENDENCIES) > 0:
    INSTALL_REQUIREMENTS.extend(NMSP_PKG_DEPENDENCIES)

NMSP_PACKAGES = ['yangkit', 'yangkit.models']
YANGKIT_PACKAGES = find_packages()

DESCRIPTION = "$DESCRIPTION$"
LONG_DESCRIPTION = "$LONG_DESCRIPTION$"

setup(
    name=NMSP_PKG_NAME,
    version=NMSP_PKG_VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/yang-infra/yangkit',
    author='Cafy',
    author_email='cafy-support@cisco.com',
    packages=YANGKIT_PACKAGES,
    namespace_packages=NMSP_PACKAGES,
    install_requires=INSTALL_REQUIREMENTS,
    include_package_data=True
)
