import errno
import platform
import os
import shutil

import subprocess
from jinja2 import Template

from . import pkgmanagers


def linux_dist():
    dist = platform.linux_distribution()
    if not dist[0]:
        if os.path.exists('/etc/arch-release'):
            return 'arch'
    return dist[0].lower()


def get_pkgtype(distro=None):
    if distro is None:
        distro = linux_dist()
    if not distro:
        return None

    if distro in ('arch', ):
        return 'pacman'
    elif distro in ('ubuntu', 'debian', ):
        return 'deb'
    elif distro in ('centos', ):
        return 'rpm'


def get_pkgman(distro=None):
    if distro is None:
        distro = linux_dist()
    if not distro:
        return None

    if distro in ('arch', ):
        return 'pacman'
    elif distro in ('ubuntu', 'debian', ):
        return 'apt-get'
    elif distro in ('centos', ):
        return 'yum'


def get_pkgman_class(name):
    if name == 'pacman':
        return pkgmanagers.Pacman
    elif name == 'apt-get':
        return pkgmanagers.AptGet
    elif name == 'yum':
        return pkgmanagers.Yum


def get_import(name):
    module, name = name.rsplit('.', 1)
    _temp = __import__(module, fromlist=[name])
    return getattr(_temp, name)


def produce_script(script, destination, context=None):
    max_filename = 255
    if len(script) < max_filename and os.path.isfile(script):
        with open(script) as fd:
            script = fd.read()
    if context is not None:
        script = Template(script).render(**context)
    with open(destination, 'w') as fd:
        fd.write(script)
    os.chmod(destination, 0755)


def produce_and_run_script(script, destination, context=None, workdir=None):
    produce_script(script, destination, context=context)
    if not os.path.isabs(destination):
        currdir = os.getcwd()
        destination = os.path.join(os.path.abspath(currdir), destination)
    return run_script(destination, workdir=workdir)


def run_script(cmd, workdir=None):
    if workdir:
        currdir = os.getcwd()
        os.chdir(workdir)
    print cmd
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    if workdir:
        os.chdir(currdir)
    if out:
        print out
    if err:
        print err
    if proc.returncode == 1:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return out


def rm_rf(path):
    try:
        shutil.rmtree(path)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            pass


def mkdir_p(*args):
    """mkdir -p"""
    try:
        os.makedirs(os.path.join(*args))
    except OSError:
        pass


class chroot(object):
    def __init__(self, new_root):
        self.cwd = os.getcwd()
        self.new_root = new_root
        self.real_root = os.open('/', os.O_RDONLY)

    def __enter__(self):
        os.chroot(self.new_root)

    def __exit__(self):
        os.fchdir(self.real_root)
        os.chroot('.')
        os.close(self.real_root)
        os.chdir(self.cwd)
