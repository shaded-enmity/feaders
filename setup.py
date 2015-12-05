#!/usr/bin/python
from setuptools import setup, find_packages
setup(
    name = 'feaders',
    version = '0.1.0',
    packages = find_packages(),
    scripts = ['feaders', 'feaders-server'],
    install_requires = ['requests', 'flask'],
    package_data = {
	    '': ['LICENSE', 'README.md', 'VERSION']
    },
    author = 'Pavel Odvody',
    author_email = 'podvody@redhat.com',
    description = 'Feaders is set of tools for searching for devel libraries in Fedora repositories by automatically scanning source/header files for includes',
    license = 'MIT',
    keywords = 'header rpm devel search',
    url = 'https://github.com/shaded-enmity/feaders'
)
