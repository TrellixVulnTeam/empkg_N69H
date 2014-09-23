# Empackage

Wrapper around the fpm project to automate the workflow of producing a package.
Inspired by the [Python Application Deployment with Native Packages]
(https://hynek.me/articles/python-app-deployment-with-native-packages/) article.

## Usage

```
empackage.py build.yml packager
```
The empackage command line tools receives a yaml file that specifies the
project options and the a python module that extends the BasePackager class
and implements the project build.
