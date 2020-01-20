import codecs
import os
import re

from setuptools import find_packages, setup


def get_version(filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        contents = fp.read()
    return re.search(r"__version__ = ['\"]([^'\"]+)['\"]", contents).group(1)


version = get_version(os.path.join('treehugger', '__init__.py'))

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='treehugger',
    version=version,
    description='Securely manage runtime configuration',
    long_description=long_description,
    author='Adam Johnson, Niklas Lindblad',
    author_email='sysadmin@timeout.com',
    url='https://github.com/timeoutdigital/treehugger',
    download_url = 'https://github.com/timeoutdigital/treehugger/archive/3.0.0.tar.gz',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=[
        'boto3',
        'PyYAML',
        'requests',
    ],
    python_requires='>=3.4',
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
