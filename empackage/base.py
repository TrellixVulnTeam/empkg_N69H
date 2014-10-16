"""
Base class to create project packagers
Projects should implement a class that inherits BasePackager and add any
extra required build/packaging steps
"""
from os import listdir
from os.path import join, exists, basename
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
from fabric.contrib.files import upload_template
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
        self.arch = conf.get('arch', 'all')
        self.vendor = conf.get('vendor', '')
        self.license = conf.get('license', '')
        self.maintainer = conf.get('maintainer', '')
        self.homepage = conf.get('homepage', '')
        self.description = conf.get('description', '')
        self.pkg_paths = conf.get('pkg_paths', [])
        self.build_deps = conf.get('build_deps', [])
        self.run_deps = conf.get('run_deps', [])
        self.hooks_dir = conf.get('hooks_dir', 'debian')
        self.conffiles = conf.get('conffiles', [])

        # Make opts
        self.make_opts = conf.get('make_opts', [])
        self.make_target = conf.get('make_target', [])


        # General opts
        self.prefix = self.conf.get('prefix')
        if self.conf.get('src_path'):
            self.src_path = self.conf.get('src_path')
        elif self.conf.get('inplace'):
            self.src_path = self.conf.get('prefix')
        else:
            self.src_path = join(BASE_PATH, self.app_name)
        self.pkg_path = join(BASE_PATH, 'pkg')

        # Repo opst
        self.repo = conf.get('repo')
        self.branch = conf.get('branch', 'master')
        self.repo_type = conf.get('repo_type', 'git')
        self.commit = conf.get('commit')
        self.deploy_key = conf.get('deploy_key')


    def prepare(self, skip_build_deps=False, update=False, use_path=None):
        """Prepare system, install packages and fpm"""

        print 'Preparing...'
        if self.build_deps and not skip_build_deps:
            print 'Installing packages...'
            sudo('apt-get update -qq')
            sudo('apt-get install -qq {}'.format(' '.join(self.build_deps)))
            sudo('gem install fpm')

        sudo('mkdir -p {}'.format(self.prefix))
        sudo('chown -R {} {}'.format(env.user, self.prefix))
        run('mkdir -p {}'.format(self.src_path))
        sudo('chown -R {} {}'.format(env.user, self.src_path))
        sudo('echo {} > /servers/me'.format(env.user))
        if use_path:
            #sudo('rm -rf {}'.format(self.src_path))
            put('{}/*'.format(use_path), self.src_path)
        elif self.repo:
            self.checkout_project(update)
        else:
            pass

        self.build_project()


    def build_project(self):
        """Packagers need to implement the build step themselves"""
        raise NotImplementedError


    def checkout_project(self, update=False):
        """Checkout/update project from repository"""
        # Setup deploy key
        self.setup_deploy_key()

        if update and not self.commit:
            print 'Updating project...'
            if self.repo_type == 'git':
                _git_update(self.src_path)
            elif self.repo_type in ('hg', 'mercurial'):
                _hg_update(self.src_path)
        else:
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
            # Vendor
            vendor = ('--vendor {}'.format(self.vendor)
                if self.vendor else '')
            # License
            license = ('--license {}'.format(self.license)
                if self.license else '')
            # Mantainer
            maintainer = ('-m {}'.format(self.maintainer)
                if self.maintainer else '')
            # Homepage
            homepage = ('--url {}'.format(self.homepage)
                if self.homepage else '')
            # Install hooks
            run('mkdir -p {}'.format('hooks'))
            for fname in listdir(self.hooks_dir):
                upload_template(
                    join(self.hooks_dir, fname),
                    join('hooks', fname),
                    self.get_context(),
                    use_jinja=True)
            hooks_str = ' '.join(
                '{} hooks/{}'.format(opt, fname)
                for opt, fname in [
                    ('--before-remove', 'prerm'),
                    ('--after-remove', 'postrm'),
                    ('--before-install', 'preinst'),
                    ('--after-install', 'postinst'),
                ]
                if exists(join(self.hooks_dir, fname))
            )
            # Configuration files
            pconffiles = (join(self.prefix, path) for path in self.conffiles)
            conffiles = ('--config-files ' + ' --config-files '.join(pconffiles)
                if self.conffiles else '')
            # Dependencies
            deps_str = ('-d ' + ' -d '.join(self.run_deps)
                        if self.run_deps else '')
            # Package paths
            paths = '  '.join(self.pkg_paths)

            # TODO should be ignoring .git/ on fpm options
            fpm_exec = 'fpm'
            #fpm_exec = '/var/lib/gems/1.8/bin/fpm' # for deb6 need to solve this
            fpm_output = run(fpm_exec + ' '
                '-s dir '
                '-t deb '
                '-n {self.pkg_name} '
                '-v {self.version} '
                '-a {self.arch} '
                '{vendor} '
                '{license} '
                '{maintainer} '
                '{homepage} '
                '--description "\nBranch: {self.branch} Commit: {self.commit}\n{self.description}" '
                '-x "*.bak" -x "*.orig" -x ".git*" '
                '{hooks} '
                '{conffiles} '
                '{deps} {paths}'
                .format(
                    self=self,
                    vendor=vendor,
                    license=license,
                    maintainer=maintainer,
                    homepage=homepage,
                    hooks=hooks_str,
                    conffiles=conffiles,
                    deps=deps_str,
                    paths=paths,
                )
            )
            deb_name = basename(fpm_output.split('"')[-2])

            if download:
                get(deb_name, '%(basename)s')
            if push:
                pass

    def get_context(self, extra_context=None):
        context = {
            'prefix': self.prefix,
        }
        context.update(self.conf)
        if extra_context:
            context.update(extra_context)

        return context

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


def _git_clone(repo, src_path, branch='master', commit=None):
    run('git clone {} -b {} {}'
        .format(repo, branch, src_path))
    if commit:
        run('git checkout {}'.format(commit))
    _git_update(src_path)


def _hg_clone(repo, src_path, branch='master', commit=None):
    if commit:
        raise NotImplementedError( 'Selecting a commit for mercurial is not '
                'supported yet')
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
    raise NotImplementedError('Updating mercurial repos is not supported yet')
