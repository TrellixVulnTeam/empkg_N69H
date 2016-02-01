"""
Base class to create project packagers
Projects should implement a class that inherits BasePackager and add any
extra required build/packaging steps
"""
import os

from jinja2 import Template

from . import sources
from .util import (
    get_pkgman,
    get_pkgman_class,
    get_pkgtype,
    linux_dist,
    mkdir_p,
    produce_and_run_script,
    produce_script,
    rm_rf,
    run_script,
)

INSTALL_HOOKS = (
    ('--before-remove', 'pre_remove'),
    ('--after-remove', 'post_remove'),
    ('--before-install', 'pre_install'),
    ('--after-install', 'post_install'),
    ('--before-upgrade', 'pre_upgrade'),
    ('--after-upgrade', 'post_upgrade'),
)
HOOK_NAMES = [hook_name for _, hook_name in INSTALL_HOOKS]


class BasePackager(object):
    def __init__(self, conf):
        self.conf = conf
        conf['startdir'] = os.getcwd()
        self.startdir = conf['startdir']

        if os.path.isabs(conf['srcdir']):
            self.srcdir = conf['srcdir']
        else:
            self.srcdir = os.path.join(conf['startdir'], conf['srcdir'])

        if os.path.isabs(conf['pkgdir']):
            self.pkgdir = conf['pkgdir']
        else:
            self.pkgdir = os.path.join(conf['startdir'], conf['pkgdir'])

        if os.path.isabs(conf['scriptdir']):
            self.scriptdir = conf['scriptdir']
        else:
            self.scriptdir = os.path.join(conf['startdir'], conf['scriptdir'])

        self.set_pkgtype()
        self.makepkgman = None
        self.set_makepkgman()

    def set_makepkgman(self):
        if self.conf['makepkgman'] is None:
            self.conf['makepkgman'] = get_pkgman(linux_dist())
        self.makepkgman = get_pkgman_class(self.conf['makepkgman'])

    def set_pkgtype(self):
        if self.conf['pkgtype'] is None:
            self.conf['pkgtype'] = get_pkgtype(linux_dist())

    def run(self):
        self.clean()

        self.apply_context()
        self.get_makedepends()
        self.get_sources()
        if self.conf['pkgver_fcn']:
            # TODO rebuild names after this?
            print 'Running pkgver_fcn...'
            self.conf['pkgver'] = produce_and_run_script(
                self.conf['pkgver_fcn'],
                os.path.join(self.scriptdir, 'pkgver_fcn'),
                context=self.conf,
                workdir=self.srcdir,
            )

        if self.conf['prepare']:
            print 'Running prepare...'
            produce_and_run_script(
                self.conf['prepare'],
                os.path.join(self.scriptdir, 'prepare'),
                context=self.conf,
                workdir=self.srcdir,
            )

        if self.conf['build']:
            print 'Running build...'
            produce_and_run_script(
                self.conf['build'],
                os.path.join(self.scriptdir, 'build'),
                context=self.conf,
                workdir=self.srcdir,
            )

        if self.conf['check']:
            print 'Running check...'
            produce_and_run_script(
                self.conf['check'],
                os.path.join(self.scriptdir, 'check'),
                context=self.conf,
                workdir=self.srcdir,
            )

        if self.conf['package']:
            print 'Running package...'
            produce_and_run_script(
                self.conf['package'],
                os.path.join(self.scriptdir, 'package'),
                context=self.conf,
                workdir=self.startdir,
            )

        print 'Generating install hooks...'
        if self.conf['install']:
            raise NotImplementedError('Meh')
        else:
            for hook in HOOK_NAMES:
                if self.conf[hook]:
                    produce_script(
                        self.conf[hook],
                        os.path.join(self.scriptdir, hook),
                        context=self.conf,
                    )

        print self.fpm()

    def clean(self):
        rm_rf(self.srcdir)
        mkdir_p(self.srcdir)
        rm_rf(self.pkgdir)
        mkdir_p(self.pkgdir)
        rm_rf(self.scriptdir)
        mkdir_p(self.scriptdir)

    def get_makedepends(self):
        print 'Running makedepends...'
        if self.conf['makedepends']:
            self.makepkgman.install(self.conf['makedepends'])

    def apply_context(self):
        self.conf['source'] = [Template(source).render(**self.conf) for source in self.conf['source']]
        self.conf['noextract'] = [Template(noextract).render(**self.conf) for noextract in self.conf['noextract']]
        self.conf['template'] = [Template(template).render(**self.conf) for template in self.conf['template']]
        self.conf['backup'] = [Template(template).render(**self.conf) for template in self.conf['backup']]

    def get_sources(self):
        print 'Running sources...'

        # for hashname in ('md5', 'sha1', 'sha256', 'sha384', 'sha512'):
        #    if self.conf['%ssums' % hashname]:
        #        hashes = self.conf['%ssums' % hashname]
        #        break
        # else:
        #    pass
        #    # TODO raise error

        for source in self.conf['source']:
            filename = sources.get_url(source, self.srcdir)
            # TODO
            # sources.check(filename, hashes[i], hashname)
            if source not in self.conf['noextract']:
                sources.extract(os.path.join(self.srcdir, filename), self.srcdir)

            if source in self.conf['template']:
                with open(os.path.join(self.srcdir, filename), 'r') as fd:
                    template = fd.read()
                template = Template(template).render(**self.conf)
                with open(os.path.join(self.srcdir, filename), 'w') as fd:
                    fd.write(template)

    def fpm(self):
        print 'Running fpm...'
        cmd = self.get_fpm_cmd()
        fpm_output = run_script(cmd, self.pkgdir)
        return os.path.basename(fpm_output.split('"')[-2])

    def get_fpm_cmd(self):
        context = {}
        context.update(self.conf)
        context.update({
            'backup': self.backup,
            'changelog': self.changelog,
            'depends': self.depends,
            'hooks': self.hooks,
            'license': self.license,
            'maintainer': self.maintainer,
            'url': self.url,
            'vendor': self.vendor,
            'paths': '*',

        })

        cmd = ('fpm '
               '-s dir '
               '-t {pkgtype} '
               '-n {pkgname} '
               '-v {pkgver} '
               '-a {arch} '
               '--description "{pkgdesc}" '
               '-x "**/*.bak" -x "**/*.orig" -x "**/.git*" -x "**/.hg*" '
               '{backup} '
               '{changelog} '
               '{depends} '
               '{hooks} '
               '{license} '
               '{maintainer} '
               '{url} '
               '{vendor} '
               '{paths}'
               .format(**context))
        return cmd

    @property
    def backup(self):
        return '--config-files ' + ' --config-files '.join(self.conf['backup']) if self.conf['backup'] else ''

    @property
    def changelog(self):
        return '--%s-changelog %s' % (self.conf['pkgtype'], self.conf['changelog']) if self.conf['changelog'] else ''

    @property
    def depends(self):
        return '-d "' + '" -d "'.join(self.conf['depends']) + '"' if self.conf['depends'] else ''

    @property
    def hooks(self):
        args = ''
        for option_name, fname in INSTALL_HOOKS:
            hook_file = os.path.join(self.scriptdir, fname)
            if os.path.isfile(hook_file):
                args += '%s %s ' % (option_name, hook_file)
        return args

    @property
    def license(self):
        # TODO multiple licences?
        return '--license "{}"'.format(self.conf['license'][0]) if self.conf['license'] else ''

    @property
    def maintainer(self):
        return '-m "{}"'.format(self.conf['maintainer']) if self.conf['maintainer'] else ''

    @property
    def vendor(self):
        return '--vendor "%s"' % self.conf['vendor'] if self.conf['vendor'] else ''

    @property
    def url(self):
        return '--url "{}"'.format(self.conf['url']) if self.conf['url'] else ''
