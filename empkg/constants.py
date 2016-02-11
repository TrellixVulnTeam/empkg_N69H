# TODO maintainer
# TODO vendor
# TODO arch: native
BASE_CONFIG = {
    # TODO search for more specific options <option name>_<architecture>_<distro>_<distro version> or any combination?
    # New
    ##################
    'pkgtype': None,  # TODO
    # Override package manager discovery for package output
    # TODO allow override from command line
    'makepkgman': None,
    # TODO allow override from command line
    # Override package manager discovery to install makedepends dependencies
    'scriptdir': 'script',
    # Dir to output dynamically generated scripts
    'template': (),
    # An array of file names corresponding to those from the source array. Files listed here will have {} variables
    # replaced with the current context.
    'maintainer': None,
    'vendor': None,


    # Options and Directives
    #########################

    # Mandatory
    'pkgname': (),
    # TODO support array
    # Either the name of the package or an array of names for split packages. Valid characters for members of this
    # array are alphanumerics, and any of the following characters: "@ . _ + -". Additionally, names are not allowed
    # to start with hyphens or dots.

    # Mandatory
    'pkgver': None,
    # The version of the software as released from the author (e.g., 2.7.1). The variable is not allowed to contain
    # colons or hyphens.
    'pkgver_fcn': None,
    # The pkgver variable can be automatically updated by providing a pkgver_fcn() function in the PKGBUILD that outputs
    # the new package version. This is run after downloading and extracting the sources so it can use those files in
    # determining the new pkgver. This is most useful when used with sources from version control systems (see below).

    # Mandatory
    'pkgrel': None,
    # This is the release number specific to the Linux release. This allows package maintainers to make updates
    # to the package's configure flags, for example. This is typically set to 1 for each new upstream software
    # release and incremented for intermediate PKGBUILD updates. The variable is not allowed to contain hyphens.

    # Mandatory
    # TODO arch list? use system arch, makepkg.conf
    # TODO arch discovery
    'arch': None,
    # Defines on which architectures the given package is available (e.g., arch=('i686' 'x86_64')). Packages that
    # contain no architecture specific files should use arch=('any').

    'epoch': 0,
    # Used to force the package to be seen as newer than any previous versions with a lower epoch, even if the
    # version number would normally not trigger such an upgrade. This value is required to be a positive integer;
    # the default value if left unspecified is 0. This is useful when the version numbering scheme of a package
    # changes (or is alphanumeric), breaking normal version comparison logic. See pacman(8) for more information
    # on version comparisons.

    'pkgdesc': None,
    # This should be a brief description of the package and its functionality. Try to keep the description to one
    # line of text and to not use the package's name.

    'url': None,
    # This field contains a URL that is associated with the software being packaged. This is typically the project's
    # web site.

    'license': (),
    # This field specifies the license(s) that apply to the package. Commonly used licenses can be found in
    # /usr/share/licenses/common. If you see the package's license there, simply reference it in the license field
    # (e.g., license=('GPL')). If the package provides a license not available in /usr/share/licenses/common, then
    # you should include it in the package itself and set license=('custom') or license=('custom:LicenseName'). The
    # license should be placed in $pkgdir/usr/share/licenses/$pkgname/ when building the package. If multiple
    # licenses are applicable, list all of them: license=('GPL' 'FDL').

    'changelog': None,
    # Specifies a changelog file that is to be included in the package. The changelog file should end in a single
    # newline. This file should reside in the same directory as the PKGBUILD and will be copied into the package by
    # makepkg. It does not need to be included in the source array (e.g., changelog=$pkgname.changelog).

    'source': (),
    # An array of source files required to build the package. Source files must either reside in the same directory
    # as the PKGBUILD, or be a fully-qualified URL that makepkg can use to download the file. To simplify the
    # maintenance of PKGBUILDs, use the $pkgname and $pkgver variables when specifying the download location, if
    # possible. Compressed files will be extracted automatically unless found in the noextract array described
    # below.
    # Additional architecture-specific sources can be added by appending an underscore and the architecture name
    # e.g., source_x86_64=(). There must be a corresponding integrity array with checksums, e.g. md5sums_x86_64=().
    # It is also possible to change the name of the downloaded file, which is helpful with weird URLs and for
    # handling multiple source files with the same name. The syntax is: source=('filename::url').
    # makepkg also supports building developmental versions of packages using sources downloaded from version
    # control systems (VCS). For more information, see Using VCS Sources below.
    # Files in the source array with extensions .sig, .sign or, .asc are recognized by makepkg as PGP signatures and
    # will be automatically used to verify the integrity of the corresponding source file.

    'validpgpkeys': (),
    # An array of PGP fingerprints. If this array is non-empty, makepkg will only accept signatures from the keys
    # listed here and will ignore the trust values from the keyring. If the source file was signed with a subkey,
    # makepkg will still use the primary key for comparison.
    # Only full fingerprints are accepted. They must be uppercase and must not contain whitespace characters.

    'noextract': (),
    # An array of file names corresponding to those from the source array. Files listed here will not be extracted
    # with the rest of the source files. This is useful for packages that use compressed data directly.

    'md5sums': (),
    # This array contains an MD5 hash for every source file specified in the source array (in the same order).
    # makepkg will use this to verify source file integrity during subsequent builds. If SKIP is put in the array in
    # place of a normal hash, the integrity check for that source file will be skipped. To easily generate md5sums,
    #  run "makepkg -g >> PKGBUILD". If desired, move the md5sums line to an appropriate location.

    'sha1sums': (),
    'sha256sums': (),
    'sha384sums': (),
    'sha512sums': (),
    # Alternative integrity checks that makepkg supports; these all behave similar to the md5sums option described
    # above. To enable use and generation of these checksums, be sure to set up the INTEGRITY_CHECK option in
    # makepkg.conf(5).

    # groups (array)
    # An array of symbolic names that represent groups of packages, allowing you to install multiple packages by
    # requesting a single target. For example, one could install all KDE packages by installing the kde group.

    'backup': (),
    # An array of file names, without preceding slashes, that should be backed up if the package is removed or
    # upgraded. This is commonly used for packages placing configuration files in /etc. See "Handling Config Files"
    # in pacman(8) for more information.

    'depends': (),
    # TODO 'depends_<distro>_<version>':
    # An array of packages this package depends on to run. Entries in this list should be surrounded with single
    # quotes and contain at least the package name. Entries can also include a version requirement of the form
    # name<>version, where <> is one of five comparisons: >= (greater than or equal to), <= (less than or equal to),
    # = (equal to), > (greater than), or < (less than).
    # If the dependency name appears to be a library (ends with .so), makepkg will try to find a binary that depends
    # on the library in the built package and append the version needed by the binary. Appending the version
    # yourself disables automatic detection.
    # Additional architecture-specific depends can be added by appending an underscore and the architecture name
    # e.g., depends_x86_64=().

    'makedepends': (),
    # An array of packages this package depends on to build but are not needed at runtime. Packages in this list
    #  follow the same format as depends.
    # Additional architecture-specific makedepends can be added by appending an underscore and the architecture name
    # e.g., makedepends_x86_64=().

    'checkdepends': (),
    # An array of packages this package depends on to run its test suite but are not needed at runtime. Packages in
    # this list follow the same format as depends. These dependencies are only considered when the check() function
    # is present and is to be run by makepkg.
    # Additional architecture-specific checkdepends can be added by appending an underscore and the architecture
    # name e.g., checkdepends_x86_64=().

    'optdepends': (),
    # An array of packages (and accompanying reasons) that are not essential for base functionality, but may be
    # necessary to make full use of the contents of this package. optdepends are currently for informational
    # purposes only and are not utilized by pacman during dependency resolution. The format for specifying
    # optdepends is:
    # optdepends=('python: for library bindings')
    # Additional architecture-specific optdepends can be added by appending an underscore and the architecture name
    # e.g., optdepends_x86_64=().

    'conflicts': (),
    # An array of packages that will conflict with this package (i.e. they cannot both be installed at the same
    # time). This directive follows the same format as depends. Versioned conflicts are supported using the
    # operators as described in depends.
    # Additional architecture-specific conflicts can be added by appending an underscore and the architecture name
    # e.g., conflicts_x86_64=().

    'provides': (),
    # An array of "virtual provisions" this package provides. This allows a package to provide dependencies other
    # than its own package name. For example, the dcron package can provide cron, which allows packages to depend on
    # cron rather than dcron OR fcron.
    # Versioned provisions are also possible, in the name=version format. For example, dcron can provide cron=2.0 to
    # satisfy the cron>=2.0 dependency of other packages. Provisions involving the > and < operators are invalid as
    # only specific versions of a package may be provided.
    # If the provision name appears to be a library (ends with .so), makepkg will try to find the library in the
    # built package and append the correct version. Appending the version yourself disables automatic detection.
    # Additional architecture-specific provides can be added by appending an underscore and the architecture name
    #  e.g., provides_x86_64=().

    'replaces': (),
    # An array of packages this package should replace. This can be used to handle renamed/combined packages. For
    # example, if the j2re package is renamed to jre, this directive allows future upgrades to continue as expected
    # even though the package has moved. Versioned replaces are supported using the operators as described in
    # depends.
    # Sysupgrade is currently the only pacman operation that utilizes this field. A normal sync or upgrade will not
    # use its value.
    # Additional architecture-specific replaces can be added by appending an underscore and the architecture name
    # e.g., replaces_x86_64=().

    'options': (),
    # https://www.archlinux.org/pacman/PKGBUILD.5.html

    # Packaging Functions
    ########################
    # In addition to the above directives, PKGBUILDs require a set of functions that provide instructions to build
    # and install the package. As a minimum, the PKGBUILD must contain a package() function which installs all the
    # package's files into the packaging directory, with optional prepare(), build(), and check() functions being
    # used to create those files from source.

    # NOTE: I want this to be able to be a bash or python script or a file
    'package': None,
    # The package() function is used to install files into the directory that will become the root directory of the
    # built package and is run after all the optional functions listed below. The packaging stage is run using
    # fakeroot to ensure correct file permissions in the resulting package. All other functions will be run as the
    # user calling makepkg.

    'prepare': None,
    # An optional prepare() function can be specified in which operations to prepare the sources for building, such
    # as patching, are performed. This function is run after the source extraction and before the build() function.
    # The prepare() function is skipped when source extraction is skipped.

    'build': None,
    # The optional build() function is use to compile and/or adjust the source files in preparation to be installed
    # by the package() function. This is directly sourced and executed by makepkg, so anything that Bash or the
    # system has available is available for use here. Be sure any exotic commands used are covered by the 'makedepends'
    #  array.
    # If you create any variables of your own in the build() function, it is recommended to use the Bash local
    # keyword to scope the variable to inside the build() function.

    'check': None,
    # An optional check() function can be specified in which a package's test-suite may be run. This function is run
    # between the build() and package() functions. Be sure any exotic commands used are covered by the checkdepends
    # array.


    # All of the above variables such as $pkgname and $pkgver are available for use in the build() function. In
    # addition, makepkg defines the following variables for use during the build and install process:
    'startdir': None,
    # This contains the absolute path to the directory where the PKGBUILD is located, which is usually the output
    # of $(pwd) when makepkg is started. Use of this variable is deprecated and strongly discouraged.

    'srcdir': 'src',
    # This points to the directory where makepkg extracts or symlinks all files in the source array.

    'pkgdir': 'pkg',
    # This points to the directory where makepkg bundles the installed package, which becomes the root directory of
    # your built package.

    # All of them contain absolute paths, which means, you do not have to worry about your working directory if you
    # use these variables properly.

    # Install/Upgrade/Remove Scripting
    ###################################

    # Pacman has the ability to store and execute a package-specific script when it installs, removes, or upgrades a
    # package. This allows a package to configure itself after installation and perform an opposite action upon
    # removal.
    # The exact time the script is run varies with each operation, and should be self-explanatory. Note that during
    # an upgrade operation, none of the install or remove scripts will be called.
    # Scripts are passed either one or two "full version strings", where a full version string is either
    # pkgver-pkgrel or epoch:pkgver-pkgrel, if epoch is non-zero.

    'pre_install': None,
    # pre_install
    # Run right before files are extracted. One argument is passed: new package full version string.

    'post_install': None,
    # post_install
    # Run right after files are extracted. One argument is passed: new package full version string.

    'pre_upgrade': None,
    # pre_upgrade
    # Run right before files are extracted. Two arguments are passed in this order: new package full version string,
    # old package full version string.

    'post_upgrade': None,
    # post_upgrade
    # Run after files are extracted. Two arguments are passed in this order: new package full version string, old
    # package full version string.

    'pre_remove': None,
    # pre_remove
    # Run right before files are removed. One argument is passed: old package full version string.

    'post_remove': None,
    # post_remove
    # Run right after files are removed. One argument is passed: old package full version string.

    'install': None,  # TODO
    # Specifies a special install script that is to be included in the package. This file should reside in the same
    # directory as the PKGBUILD and will be copied into the package by makepkg. It does not need to be included in
    # the source array (e.g., install=$pkgname.install).
    # To use this feature, create a file such as pkgname.install and put it in the same directory as the PKGBUILD
    # script. Then use the install directive:
    # install=pkgname.install

    # The install script does not need to be specified in the source array. A template install file is available in
    # /usr/share/pacman as proto.install for reference with all of the available functions defined.
}
