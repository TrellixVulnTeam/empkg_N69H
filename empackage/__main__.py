#! /usr/bin/env python2
from __future__ import (division, absolute_import, print_function,
    unicode_literals)

"""Commnad line tool to build a package"""
import argparse
import importlib
import os
import sys

import yaml
from fabric.api import env, execute
from fabric.api import sudo, get, put, cd, local
from fabtools.vagrant import ssh_config, _settings_dict

EXIT_OK = 0
EXIT_FAILED = 1

def vagrant(name=''):
    """Setup fabric to use vagrant"""
    config = ssh_config(name)
    extra_args = _settings_dict(config)
    env.update(extra_args)


example_config = """
# Package basic info
####################################
name: example
version: 1.1.0
maintainer: example@example.com
homepage: https://example.com
description: What does it do
# Changelog
#changelog:
# Architecture (ex: i86, x64, native)
#arch: all
# Package vendor, optional
#vendor:
# License (ex: GPL), optional
#license:

# Build target
###################################
# Hostname/ip of the target machine to perform the build
# Note: this can be defined in the ~/.empackage file and overriden with the
# --target cli argument.
#target: 

# Repository/Src location
###################################
# Note: these options can be overridden user the --src cli argument
# Source location, optional
#src:
# Repository URL, optional
#repo:
# Version control app (ex: git, hg)
#repo_type: git
# Repo branch
#branch:
# Repo commit
#commit:
# Deploy key to checkout from repo, optional
#deploy_key:

# Package Repository
###################################
# Repository to upload package to, optional
# Note: Package will only be pushed to the repo using the --push cli argument.
#       This parameter can be defined in the ~/.empackage file and overriden
#       with the --pkg-repo cli argument
pkg_repo: repo.example.com:/repo/development/wheezy

# Package config
###################################
# Note: Any file/dir in the templates directory will be copied to the package
# Package format (ex: deb, rpm)
#pkg_type: deb
# Paths (dir or file) to include in the package, defaults to prefix
#pkg_paths: <prefix>
# Paths to directory containing install hook scripts
#hooks_dir: hooks
# Paths to config files, relative paths start from prefix
#config_files:
# Extra directories to create
# extra_dirs

# Build config
###################################
# Make cmd prefix, also used for relative paths
#prefix:
# Build dependencies, optional
#build_deps:
# Pip build dependencies, optional
# pip_build_deps:
# Pip Requires, if true expects templates/requirements.txt and will pip install it
# after creating the virtualenv (use it to pin versions to good knowns)
# or use python_requires if you don't want a requirements.txt
# pip_requires:
# Package runtime dependencies
#run_deps:
# Where to place project source
#src_path: /tmp/<pkg_name>
# Place project directly on <prefix>
#inplace: False
# Use predifined build profile (ex: python, make), optional
#profile:
# Python requires, `python` profile, optional
#python_requires:
# Python virtualenv, `python` profile
#python_virtualenv: True
#python_requires:
# Make options, `make` profile, optional
#make_opts:
# Make target, `make` profile, optional
# make_target: install

# Extra vars
###################################
# Any extra config option defined here will be available in you custom packager
# implementation

"""

parser = argparse.ArgumentParser('Commnad line tool for compiling and building packages')
parser.add_argument('--config',
        default='build.yml',
        help='Select a diferent config file')
parser.add_argument('--packager',
        default='packager',
        help='Select a diferent custom packager module')
parser.add_argument('--pythonpath',
        default='',
        help='Add to python path')
parser.add_argument('--gen-config',
        action='store_true',
        help='Create example config file')

parser.add_argument('--get',
        action='store_true',
        help='Get package')
parser.add_argument('--push',
        action='store_true',
        help='Push to package repository (scp format)')

parser.add_argument('--no-clean-pkg-paths',
        action='store_true',
        help="Don't clear package paths")
parser.add_argument('--no-check-build-deps',
        action='store_true',
        help="Don't check/install build dependencies")
parser.add_argument('--no-clean-checkout',
        action='store_true',
        help="Only update if project is already checked out")

parser.add_argument('--pkg-repo',
        default=None,
        help='Set/Override package repo path')
parser.add_argument('--src',
        default=None,
        help='Use a path for src code')
parser.add_argument('--target',
        default=None,
        help='Hostname of the build target')

def main(args=None):
    exitstatus = EXIT_OK
    if args is None:
        args = vars(parser.parse_args())

    if args.get('gen_config'):
        print(example_config)
        return exitstatus

    pythonpath = args.pop('pythonpath')
    if pythonpath:
        sys.path = pythonpath.split(',') + sys.path
    if '' not in sys.path:
        sys.path.insert(0, '')


    config = {}
    # Load user config
    try:
        fd = open(os.path.expanduser('~/.empackage'))
    except IOError:
        pass
    else:
        config.update(yaml.safe_load(fd))
        fd.close()

    # Config file options
    config_file = args.pop('config')
    if config_file:
        try:
            fd = open(config_file)
        except IOError:
            pass
        else:
            config.update(yaml.safe_load(fd))
            fd.close()

    # Environment options
    for key in args.keys():
        value = os.environ.get('EMPACKAGE_{}'.format(key.upper()))
        if value is not None:
            config[key] = value

    # Cli options
    for key, value in args.iteritems():
        if value is not None:
            config[key] = value

    # TODO check required config options (target, etc)
    if 'target' not in config or not config['target']:
        print('Build target must be defined')
        exitstatus = EXIT_FAIL
        return exitstatus

    target = config.pop('target')


    # Configure build target
    # TODO enable localhost
    if target == 'vagrant':
        vagrant()
    else:
        env.use_ssh_config = True
        env.hosts = [target, ]

    execute(build, config)
    return exitstatus


def build(config):
    """Initiate fabric task to build package"""
    get_pkg = config.pop('get')
    push_pkg = config.pop('push')
    profile = config.get('profile')
    no_check_build_deps = config.pop('no_check_build_deps')

    if profile:
        if profile == 'python':
            packager = importlib.import_module('empackage.packager').PythonPackager(config)
        elif profile == 'make':
            packager = importlib.import_module('empackage.packager').MakePackager(config)
    else:
        packager_module = config.pop('packager')
        packager = importlib.import_module(packager_module).Packager(config)

    if not no_check_build_deps:
        packager.install_build_dependencies()
    packager.prepare()
    packager.build()
    packager.makepkg()

    if get_pkg:
        with cd(packager.conf['tmp_remote_dir']):
            get(packager.pkg_name, '%(basename)s')
    if push_pkg:
        # TODO improve
        with cd(packager.conf['tmp_remote_dir']):
            get(packager.pkg_name, '/tmp')
        pkg_repo = config.pop('pkg_repo')
        local('scp {} {}'.format(os.path.join('/tmp', packager.pkg_name), pkg_repo))
        local('rm /tmp/{}'.format(packager.pkg_name))



if __name__ == '__main__':
    errno = main()
    sys.exit(errno)

