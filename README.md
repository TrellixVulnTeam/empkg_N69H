# Empackage

## Overview

Wrapper around the fpm project to automate the workflow of producing system
packages.
Inspired by the [Python Application Deployment with Native Packages]
(https://hynek.me/articles/python-app-deployment-with-native-packages/) article.


## Installation

Install using `pip`...
```
pip install empackage
```

User settings can be placed in the user home under `~/.empackage`, example:

```

---

target: <build vm hostname>
pkg_repo: <scp style path to repo>
```

## Usage

Create a directory for the package settings/files and generate a configuration
skeleton.
```
mkdir packager
cd packager
empackage --gen-config > build.yaml
```
By default install hooks sould be located in the `hooks` directory and files
that should be copied to over in the `templates` directory.


