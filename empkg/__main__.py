import argparse
import logging
import os
import re
import sys
from copy import copy

import yaml
from fabric.api import (
    cd,
    env,
    execute,
    get,
    put,
    run,
    sudo,
)
from fabric.contrib.files import exists

from .__init__ import __description__ as description
from .constants import BASE_CONFIG
from .packagers import BasePackager
from .util import rm_rf, get_pkgman_class, get_pkgman

logging.basicConfig(level=logging.INFO)

EXIT_OK = 0
EXIT_FAIL = 1


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('pkgbuild')
    parser.add_argument('--target')  # remote build target
    parser.add_argument('--pkgman', action='store_true')  # remote build target
    parser.add_argument('--makepkgman', action='store_true')  # remote build target
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--dev', action='store_true')  # TODO dev removes checksum check (when I implement the check)
    pargs = parser.parse_args(args)

    conf = copy(BASE_CONFIG)
    with open(os.path.expanduser(pargs.pkgbuild)) as fd:
        conf.update(yaml.safe_load(fd))

    if pargs.clean:
        rm_rf(conf['srcdir'])
        rm_rf(conf['pkgdir'])
        rm_rf(conf['scriptdir'])
        rm_rf(conf['hookdir'])
        return None

    if pargs.target:
        # TODO deploy keys
        env.use_ssh_config = True
        env.hosts = [pargs.target, ]

        # Remove target
        new_args = []
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg == '--target':
                skip = True
                continue

            new_args.append(arg)
            skip = False

        execute(remote_package, new_args, conf)
    else:
        packager = BasePackager(conf)
        packager.run()

    return None


def remote_package(args, conf):
    remote_install(args)

    remotedir = '/tmp/%s' % conf['pkgname']
    run('rm -rf %s' % remotedir)
    run('mkdir -p %s' % remotedir)
    put(local_path='*', remote_path=remotedir)
    with cd(remotedir):
        out = run('empkg %s' % ' '.join(args))
        pkgname = out.split('\n')[-1]
        get(remote_path=os.path.join(remotedir, conf['pkgdir'], pkgname), local_path='.')


def remote_install(args):
    distro = remote_linux_dist()
    depends = ()
    if distro == 'arch':
        # TODO if yaourt available use to install fpm?
        # TODO arch depends
        depends = ()
    elif distro in ('debian', 'ubuntu'):
        depends = (
            'build-essential',
            'openssl',
            'libssl-dev',
            'ruby',  # fpm
            'ruby-dev',  # fpm
            'python-pip',
            'libyaml-dev',  # PyYAML
            'python-dev',  # PyYAML
        )
    elif distro == 'centos':
        depends = ('gcc', 'gcc-c++', 'kernel-devel', 'openssl', 'openssl-devel', 'ruby', 'ruby-devel', 'rubygems',
                   'rpm', 'rpm-build', )  # TODO centos pip?
    pkgman = get_pkgman_class(get_pkgman(distro))
    sudo(pkgman.install_cmd % ' '.join(depends))

    # TODO try to update fpm?
    out = run('gem list')
    pattern = re.compile(r'^fpm ', re.MULTILINE)
    if not re.search(pattern, out):
        sudo('gem install fpm')

    # TODO dev/prod mode switch
    if any(('--dev' == arg for arg in args)):
        sudo('pip install -U --force-reinstall --no-deps empkg')
    else:
        sudo('pip install -U empkg')


def remote_linux_dist():
    out = eval(run('python -c "import platform; print(platform.linux_distribution())"', shell=True))
    if not out[0]:
        if exists('/etc/arch-release'):
            return 'arch'
    return out[0].lower()


if __name__ == '__main__':
    err = main()
    if err:
        logging.warning("Exiting with message %s", err)
        sys.exit(EXIT_FAIL)
    sys.exit(EXIT_OK)
