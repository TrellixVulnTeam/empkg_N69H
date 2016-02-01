#! /usr/bin/env python
import codecs
import os
import re

from setuptools import setup, find_packages


def read_file(filename, encoding='utf8'):
    with codecs.open(filename, encoding=encoding) as fd:
        return fd.read()

here = os.path.abspath(os.path.dirname(__file__))
init = os.path.join(here, 'empkg', '__init__.py')
meta = dict(re.findall(r"__([a-z_]+)__ = '([^']+)", read_file(init)))

setup(
    name='empkg',
    version=meta['version'],
    license=meta['license'],
    description=meta['description'],
    long_description=read_file('README.md'),
    url=meta['url'],

    author=meta['author'],
    author_email=meta['author_email'],

    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyYAML',
        'Fabric',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'empkg = empkg.__main__:main',
        ]
    },
)
