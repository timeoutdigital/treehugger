# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('treehugger')

with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='treehugger',
    version=version,
    description='Securely manage runtime configuration',
    long_description=long_description,
    author='Adam Johnson, Niklas Lindblad',
    author_email='sysadmin@timeout.com',
    url='https://github.com/timeoutdigital/treehugger',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=[
        'boto3',
        'PyYAML',
        'requests',
        'six',
    ],
    license='ISC License',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'treehugger = treehugger.__main__:main'
        ]
    },
    keywords='',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
