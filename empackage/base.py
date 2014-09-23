"""
Base class to create project packagers
Projects should implement a class that inherits BasePackager and add any
extra required build/packaging steps
"""
import os
from fabric.api import (
    settings,
    run,
    local,
    cd,
    env,
    sudo,
    put,
    shell_env,
    get,
    hide,
)
from fabtools.files import is_dir


BASE_PATH = "/tmp/"

class BasePackager(object):
    """
    Base class to create project packagers
    Projects should implement a class that inherits BasePackager and add any
    extra required build/packaging steps
    """
    def __init__(self, conf):
        self.conf = conf

        self.app_name = conf.get('app_name')
        self.pkg_name = self.app_name
        self.version = conf.get('version', '1.0')

        self.pkg_paths = conf.get('pkg_paths', [])
        self.build_deps = conf.get('build_deps', [])
        self.run_deps = conf.get('run_deps', [])

        self.make_opts = conf.get('make_opts', [])
        self.make_target = conf.get('make_target', [])

        self.src_path = os.path.join(BASE_PATH, self.app_name)
        self.pkg_path = os.path.join(BASE_PATH, 'pkg')

        self.repo = conf.get('repo')
        self.branch = conf.get('branch', 'master')
        self.repo_type = conf.get('repo_type', 'git')

        self.deploy_key = conf.get('deploy_key')
        self.debian_scripts = conf.get('debian_scripts')


    def prepare(self, skip_packages=False, update=False):
        """Prepare system, install packages and fpm"""

        print 'Preparing...'
        if self.build_deps and not skip_packages:
            print 'Installing packages...'
            sudo('apt-get update -qq')
            sudo('apt-get install -qq {}'.format(' '.join(self.build_deps)))
            sudo('gem install fpm')

        self.checkout_project(update)
        self.build_project()


    def build_project(self):
        """Packagers need to implement the build step themselves"""
        raise NotImplementedError


    def checkout_project(self, update=False):
        """Checkout/update project from repository"""
        # Setup deploy key
        self.setup_deploy_key()

        if not update:
            print 'Checking out project...'

            # Clear/create app dir
            sudo('rm -rf {}'.format(self.src_path))
            sudo('mkdir -p {}'.format(self.src_path))
            sudo('chown {0}.{0} {1}'.format(env.user, self.src_path))

            # Clone repo
            if self.repo_type == 'git':
                _git_clone(self.repo, self.src_path, self.branch)
            elif self.repo_type in ('hg', 'mercurial'):
                _hg_clone(self.repo, self.src_path, self.branch)
        else:
            print 'Updating project...'
            if self.repo_type == 'git':
                _git_update(self.src_path)
            elif self.repo_type in ('hg', 'mercurial'):
                _hg_update(self.src_path)

        if self.repo_type == 'git':
            self.commit = _current_git_commit(self.src_path)
        elif self.repo_type in ('hg', 'mercurial'):
            self.commit = _current_hg_commit(self.src_path)


    def setup_deploy_key(self):
        """Setup deploy key"""
        if self.deploy_key:
            with settings(hide('running', 'warnings'), warn_only=True):
                if run('[ ! -d ~/.ssh ]').succeeded:
                    run('mkdir ~/.ssh')
            put(self.deploy_key, '~/.ssh/id_rsa', mirror_local_mode=True)


    def build_pkg(self, push=False, download=True):
        """Build package"""
        print 'Building package...'

        run('rm -rf {}'.format(self.pkg_path))
        run('mkdir -p {}'.format(self.pkg_path))
        with cd(self.pkg_path):
            # Debian installation scripts
            put(local_path=self.debian_scripts,
                remote_path=self.pkg_path)

            deps_str = ('-d ' + ' -d '.join(self.run_deps)
                        if self.run_deps else '')
            hooks_str = ' '.join(
                '{} debian/{}'.format(opt, fname)
                for opt, fname in [
                    ('--before-remove', 'prerm'),
                    ('--after-remove', 'postrm'),
                    ('--before-install', 'preinst'),
                    ('--after-install', 'postinst'),
                ]
                if os.path.exists(os.path.join('debian', fname))
            )
            paths = '  '.join(self.pkg_paths)
            fpm_output = run('fpm '
                '-s dir '
                '-t deb '
                '-n {self.pkg_name} '
                '-v {self.version} '
                '-a all '
                '-x "*.bak" -x "*.orig" -x ".git*" '
                '{hooks} '
                '--description '
                '"Branch: {self.branch} Commit: {self.commit}" '
                '{deps} {paths}'
                .format(self=self, hooks=hooks_str, deps=deps_str,
                        paths=paths))
            deb_name = os.path.basename(fpm_output.split('"')[-2])

            if download:
                get(deb_name, '%(basename)s')
            if push:
                pass


def _current_git_branch(src_path):
    with cd(src_path):
        return run('git symbolic-ref HEAD')[11:]


def _current_hg_branch(src_path):
    pass


def _current_git_commit(src_path):
    with cd(src_path):
        return run('git rev-parse --short HEAD')


def _current_hg_commit(src_path):
    pass


def _git_clone(repo, src_path, branch='master'):
    run('git clone {} -b {} {}'
        .format(repo, branch, src_path))
    _git_update(src_path)


def _hg_clone(repo, src_path, branch='master'):
    cmd = 'hg clone {}'.format(repo)
    if branch:
        cmd = '{}#{}'.format(cmd, branch)
    cmd = '{} {}'.format(cmd, src_path)
    run(cmd)


def _git_update(src_path):
    with cd(src_path):
        run('git pull')
        run('git submodule init')
        run('git submodule update')


def _hg_update(src_path):
    pass
