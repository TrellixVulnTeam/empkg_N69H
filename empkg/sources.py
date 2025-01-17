import os
import tarfile
import shutil
from urllib2 import urlopen
from urlparse import urlparse


def get_url(source, destination):
    src = urlparse(source)
    filename = None
    if src.scheme in ('', 'file'):
        dest = os.path.join(destination, source)
        if not os.path.isdir(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        shutil.copy2(source, dest)
        filename = source
    elif src.scheme in ('http', 'https', 'ftp'):
        filename = download_url(source, destination)
    elif 'git' in src.scheme:
        # TODO git, git+http
        raise NotImplementedError('Git repo support')
    elif 'hg' in src.scheme:
        # TODO
        raise NotImplementedError('Mercurial repo support')
    return filename


def download_url(source, destination):
    remote = urlopen(source)
    if 'Content-Disposition' in remote.headers:
        content_disposition = remote.headers['Content-Disposition']
        filename = content_disposition.split('=')[1]
    else:
        filename = os.path.basename(source)

    with open(os.path.join(destination, filename), 'wb') as local:
        while True:
            data = remote.read(1024)
            if not data:
                break
            local.write(data)
    remote.close()
    return filename


# TODO
# def check(filename, hashvalue, hashname):
#    pass


def extract(filename, destination):
    try:
        _, extension = filename.rsplit('.', 1)
    except ValueError:
        return
    if extension in ('gz', 'bz2', 'tar'):
        with tarfile.open(filename, 'r:*') as fd:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(fd, destination)
    elif extension in ('zip', ):
        # TODO
        raise NotImplementedError('Zip support')
