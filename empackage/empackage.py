#! /usr/bin/env python
"""Commnad line tool to build a package"""

import importlib
import os
import sys

from fabric.api import env, execute
from fabtools.vagrant import ssh_config, _settings_dict
import click
import yaml


def vagrant(name=''):
    """Setup fabric to use vagrant"""
    config = ssh_config(name)
    extra_args = _settings_dict(config)
    env.update(extra_args)


@click.command()
@click.option('--push', '-p', is_flag=True, help='Push to repo')
@click.option('--skip-build-deps', is_flag=True, help='Skip installing build packages')
@click.option('--update', is_flag=True, help='Clear app dir')
@click.option('--download', '-d', is_flag=True, help='Download package')
@click.option('--use_path', default=None,
    help='Use local directory instead of repository')
@click.option('--target', '-t', default=None, help='Set/Override build target')
@click.argument('config', default='build.yml')
@click.argument('packager', default='packager')
def main(
        push,
        skip_build_deps,
        update,
        download,
        use_path,
        target,
        config,
        packager
    ):
    """Build and package"""
    extension = os.path.splitext(config)[1]
    if extension in ('.yml', '.yaml'):
        config = yaml.safe_load(open(config))
    elif extension == ('.py', ''):
        if extension == '.py':
            config = config[:3]
        config = import_module(config)['config']
    else:
        raise NotImplementedError(
            'No loader defined for filetype {}'.format(extension)
        )

    if 'target' not in config and target is None:
        print 'Build target must be defined either in the config or the cmd line'
        sys.exit(1)

    if 'target' in config and config['target'] == 'vagrant':
        vagrant()
    else:
        env.use_ssh_config = True
        if target is not None:
            env.hosts = [target, ]
        else:
            env.hosts = [config['target'], ]

    if packager.endswith('.py'):
        packager = packager[:-3]

    execute(
        build,
        push, skip_build_deps, update, download, use_path, config, packager)


def build(push, skip_build_deps, update, download, use_path, config, packager):
    """Initiate fabric task to build package"""
    sys.path.insert(0, '.')
    packager = importlib.import_module(packager)
    pkgr = packager.Packager(config)
    pkgr.prepare(skip_build_deps, update, use_path)
    pkgr.build_pkg(push=push, download=download)

    if push:
        pkr.push_to_pkg_repo()


if __name__ == '__main__':
    main()
