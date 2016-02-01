import subprocess


class BasePackageManger(object):
    @classmethod
    def install(cls, packages):
        raise NotImplementedError()


class Pacman(BasePackageManger):
    # TODO uncomment
    # install_cmd = 'sudo pacman -Sq --noconfirm %s'
    install_cmd = 'sudo pacman -Sq %s'

    @classmethod
    def install(cls, packages):
        cmd = cls.install_cmd % ' '.join(packages)
        subprocess.call(cmd, shell=True)

    # TODO set packager https://wiki.archlinux.org/index.php/makepkg#Packager_information


class AptGet(BasePackageManger):
    install_cmd = 'sudo apt-get install -qq %s'

    @classmethod
    def install(cls, packages):
        cmd = cls.install_cmd % ' '.join(packages)
        subprocess.call(cmd, shell=True)


class Yum(BasePackageManger):
    install_cmd = 'sudo yum install -y -q %s'

    @classmethod
    def install(cls, packages):
        cmd = cls.install_cmd % ' '.join(packages)
        subprocess.call(cmd, shell=True)
