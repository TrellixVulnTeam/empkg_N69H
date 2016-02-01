# Empackage

## Overview

Wrapper around the fpm project create packages using PKGBUILD sintax.


## Installation

Install using `pip`...
```
pip install empkg
```

## Usage

Create a yml config file for the package. Check constants.py for available options and meanings. Run `empkg` on the config file, for example building a package on a remote server would be:
```
empkg PKGBUILD.yml --target <hostname>
```


