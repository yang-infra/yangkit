"""
Setup for yangkit model bundle
$PACKAGE$
"""

from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

INSTALL_REQUIREMENTS = ['yangkit>=$CORE_VERSION$']

NMSP_PKG_NAME = "$PACKAGE$"
NMSP_PKG_VERSION = "$VERSION$"
NMSP_PKG_DEPENDENCIES = ['$DEPENDENCY$']

if len(NMSP_PKG_DEPENDENCIES) > 0:
    INSTALL_REQUIREMENTS.extend(NMSP_PKG_DEPENDENCIES)

NMSP_PACKAGES = ['yangkit', 'yangkit.models']
YANGKIT_PACKAGES = find_packages(exclude=['contrib', 'docs*', 'tests*',
                                      'ncclient', 'samples'])

DESCRIPTION = "$DESCRIPTION$"
LONG_DESCRIPTION = "$LONG_DESCRIPTION$"

setup(
    name=NMSP_PKG_NAME,
    version=NMSP_PKG_VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/CiscoDevNet/ydk-py',
    author='Cisco Systems',
    author_email='yang-dk@cisco.com',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: C++'
    ],
    keywords='yang, C++11,  python bindings',
    packages=YANGKIT_PACKAGES,
    namespace_packages=NMSP_PACKAGES,
    install_requires=INSTALL_REQUIREMENTS,
    include_package_data=True
)
