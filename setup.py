#! /usr/bin/env python
from setuptools import setup, find_packages


setup(
    name="empackage",
    version="0.1",
    packages=find_packages(),
    scripts=['empackage.py'],
    include_package_data=True,
    install_requires=[
        'Fabric>=1.9.1',
        'fabtools>=0.19.0',
        'PyYAML>=3.11',
        'click==3.2',
    ],
    entry_points={
        'console_scripts': 'empackage = empackage:main'
    },

    author='Hugo Castilho',
    author_email='hugo.p.castilho@telecom.pt',
    description='Wrapper for fpm to produce native packages',
    keywords=['package', 'fpm'],
    long_description="""
    This package is a wrapper around fpm in the style described in:
    https://hynek.me/articles/python-app-deployment-with-native-packages/
    """
)

