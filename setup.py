#! /usr/bin/env python
from setuptools import setup, find_packages


setup(
    name="empackage",
    version="0.6.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Fabric',
        'fabtools',
        'PyYAML',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'empackage = empackage.__main__:main',
        ]
    },

    author='Hugo Castilho',
    author_email='hugo.p.castilho@telecom.pt',
    url='https://gitlab.intra.sapo.pt/security/empackage',
    description='Wrapper for fpm to produce native packages',
    keywords=['package', 'fpm'],
    long_description="""
    This package is a wrapper around fpm in the style described in:
    https://hynek.me/articles/python-app-deployment-with-native-packages/
    """
)

