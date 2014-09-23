#! /usr/bin/env python

import importlib
import os
import sys

from fabric.api import env, execute
from fabtools.vagrant import ssh_config, _settings_dict
import click
import yaml


def vagrant(name=''):
    config = ssh_config(name)
    extra_args = _settings_dict(config)
    env.update(extra_args)


@click.command()
@click.option('--push', '-p', is_flag=True,
        help='Push to repo')
@click.option('--skip-packages', is_flag=True,
        help='Skip installing packages')
@click.option('--update', is_flag=True,
        help='Clear app dir')
@click.option('--download', '-d', is_flag=True,
        help='Download package')
@click.argument('config', default='build.yml')
@click.argument('packager', default='packager')
def main(push, skip_packages, update, download, config, packager):
    """Build and package"""
    config = yaml.safe_load(open(config))
    if config['target'] == 'vagrant':
        vagrant()
    else:
        env.hosts = [config['target'], ]

    if packager.endswith('.py'):
        packager = packager[:-3]

    execute(build, push, skip_packages, update, download, config, packager)


def build(push, skip_packages, update, download, config, packager):
    sys.path.insert(0, '.')
    packager = importlib.import_module(packager)
    pkgr = packager.Packager(config)
    pkgr.prepare(skip_packages, update)
    pkgr.build_pkg(push=push, download=download)

    if push:
        pkr.push_to_pkg_repo()


if __name__ == '__main__':
    main()
