"""
Base class to create project packagers
Projects should implement a class that inherits BasePackager and add any
extra required build/packaging steps
"""
from os import listdir
from os.path import join, exists, basename, isdir, isfile
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
from fabtools.files import is_dir, is_file


BASE_PATH = "/tmp/"

class BasePackager(object):
    """
    Base class to create project packagers
    Projects should implement a class that inherits BasePackager and add any
    extra required build/packaging steps

    Package Options:
    app_name -- Application name, used to name the package
    pkg_type -- Comma sepparated list of package types to produce (default 'deb')
    pkg_dest -- Where to place the package (default '/tmp/pkg/')
    version -- Package version (default 1.0)
    arch -- Architecture (default 'all')
    vendor -- Vendor (default '')
    license
    maintainer
    homepage
    description
    changelog -- Changelog file
    pkg_src_paths -- Aditional (besides prefix) paths that sould be included in
                the package
    build_deps -- Build dependencies
    run_depes -- Package runtime dependencies
    hooks_dir -- Path to install hooks
    config_files -- Mark files as configuration

    Repository Options:
    repo -- Repository URL
    repo_type -- Repository type (defaults 'git')
    branch -- Branch to checkout (defaults 'master')
    commit -- Commit to checkout (defaults 'HEAD')
    deploy_key -- Key to checkout repository

    Build Options:
    prefix -- Project prefix, relative paths will start here
    src_path -- Where to place project src (defaults '/tmp/<app_name>')
    inplace -- If set project is moved directly to prefix
    make_opts -- Make options (to use in self.build_project)
    make_target -- Make target (to use in self.build_project)


    """
    def __init__(self, conf):
        self.conf = conf
        # Package Options
        self.app_name = conf.get('app_name')
        self.pkg_name = self.app_name
        self.pkg_types = conf.get('pkg_types', 'deb').split(',')
        self.pkg_path = join(BASE_PATH, 'pkg', self.app_name)
        self.version = conf.get('version', '1.0')
        self.arch = conf.get('arch', 'all')
        self.vendor = conf.get('vendor', '')
        self.license = conf.get('license', '')
        self.maintainer = conf.get('maintainer', '')
        self.homepage = conf.get('homepage', '')
        self.description = conf.get('description', '')
        self.changelog = conf.get('changelog', '')
        self.pkg_src_paths = conf.get('pkg_src_paths', [])
        self.build_deps = conf.get('build_deps', [])
        self.run_deps = conf.get('run_deps', [])
        self.hooks_dir = conf.get('hooks_dir', 'debian')
        self.config_files = conf.get('config_files', [])
        self.tmp_remote_dir = join(BASE_PATH, 'tmp_{}'.format(self.app_name))
        # Build Options
        self.make_opts = conf.get('make_opts', [])
        self.make_target = conf.get('make_target', [])
        self.prefix = self.conf.get('prefix')
        if self.conf.get('src_path'):
            self.src_path = self.conf.get('src_path')
        elif self.conf.get('inplace'):
            self.src_path = self.conf.get('prefix')
        else:
            self.src_path = join(BASE_PATH, self.app_name)
        # Repo Options
        self.repo = conf.get('repo')
        self.repo_type = conf.get('repo_type', 'git')
        self.branch = conf.get('branch', 'master')
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
        # Create root dir
        sudo('mkdir -p {}'.format(self.prefix))
        sudo('chown -R {} {}'.format(env.user, self.prefix))
        # Create dir for project src
        run('mkdir -p {}'.format(self.src_path))
        sudo('chown -R {} {}'.format(env.user, self.src_path))
        if use_path:
            # Use local path instead of a repo
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
        run('mkdir -p {}'.format(self.tmp_remote_dir))

        with cd(self.pkg_path):
            self.copy_hooks()
            self.copy_changelog()
            for pkg_type in self.pkg_types:
                cmd = self.get_fpm_cmd(pkg_type)
                fpm_output = run(cmd)
                deb_name = basename(fpm_output.split('"')[-2])

                if download:
                    get(deb_name, '%(basename)s')
                if push:
                    # TODO push to package repository
                    pass

    def get_fpm_cmd(self, pkg_type):
        fpm_exec = 'fpm'
        #fpm_exec = '/var/lib/gems/1.8/bin/fpm' # for deb6 need to solve this
        cmd = (fpm_exec + ' '
            '-s dir '
            '-t {pkg_type} '
            '-n {self.pkg_name} '
            '-v {self.version} '
            '-a {self.arch} '
            '{vendor} '
            '{license} '
            '{maintainer} '
            '{homepage} '
            '--description "{self.description}" '
            '-x "**/*.bak" -x "**/*.orig" -x "**/.git*" '
            '{changelog} '
            '{hooks} '
            '{config_files} '
            '{deps} {paths}'
            .format(
                self=self,
                pkg_type=pkg_type,
                vendor=self.get_vendor_arg(),
                license=self.get_license_arg(),
                maintainer=self.get_maintainer_arg(),
                homepage=self.get_homepage_arg(),
                hooks=self.get_hooks_arg(),
                changelog = self.get_changelog_arg(pkg_type),
                config_files=self.get_config_files_arg(),
                deps=self.get_dependencies_arg(),
                paths=self.get_package_paths_arg(),
            ))
        return cmd

    def get_changelog_arg(self, pkg_type):
        changelog_file = join(self.tmp_remote_dir, 'changelog')
        if not is_file(changelog_file):
            return ''
        if pkg_type == 'deb':
            arg = '--deb-changelog '
        elif pkg_type == 'rpm':
            arg = '--rpm-changelog '
        return arg + changelog_file

    def copy_changelog(self):
        if 'changelog' in self.conf and isfile(self.conf.get('changelog')):
            upload_template(
                self.conf['changelog'],
                join(self.tmp_remote_dir, 'changelog'),
                self.get_context(),
                use_jinja=True)
        elif self.conf.get('changelog', False) == True:
            # TODO automatic changelog
            pass

    def get_vendor_arg(self):
        arg = ('--vendor {}'.format(self.vendor) if self.vendor else '')
        return arg

    def get_license_arg(self):
        arg = ('--license {}'.format(self.license) if self.license else '')
        return arg

    def get_maintainer_arg(self):
        arg = ('-m {}'.format(self.maintainer) if self.maintainer else '')
        return arg

    def get_homepage_arg(self):
        arg = ('--url {}'.format(self.homepage) if self.homepage else '')
        return arg

    def get_config_files_arg(self):
        paths = (join(self.prefix, path) for path in self.config_files)
        arg = ('--config-files ' + ' --config-files '.join(paths)
            if self.config_files else '')
        return arg

    def get_dependencies_arg(self):
        arg = ('-d "' + '" -d "'.join(self.run_deps) + '"' if self.run_deps else '')
        return arg

    def get_package_paths_arg(self):
        paths = [self.prefix]
        paths.extend(self.pkg_src_paths)
        return ' '.join(paths)

    def get_hooks_arg(self):
        hooks_str = ''
        if not isdir(self.hooks_dir):
            return ''
        hooks_str = ' '.join(
            '{} {}/{}'.format(opt, self.tmp_remote_dir, fname)
            for opt, fname in [
                ('--before-remove', 'prerm'),
                ('--after-remove', 'postrm'),
                ('--before-install', 'preinst'),
                ('--after-install', 'postinst'),
            ]
            if exists(join(self.hooks_dir, fname))
            )
        return hooks

    def copy_hooks(self):
        if not isdir(self.hooks_dir):
            return
        for fname in listdir(self.hooks_dir):
            upload_template(
                join(self.hooks_dir, fname),
                join(self.tmp_remote_dir, fname),
                self.get_context(),
                use_jinja=True)

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
