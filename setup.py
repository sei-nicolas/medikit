# Generated by Medikit 0.7.3 on 2019-06-30.
# All changes will be overriden.
# Edit Projectfile and run “make update” (or “medikit update”) to regenerate.

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Py3 compatibility hacks, borrowed from IPython.
try:
    execfile
except NameError:

    def execfile(fname, globs, locs=None):
        locs = locs or globs
        exec(compile(open(fname).read(), fname, "exec"), globs, locs)


# Get the long description from the README file
try:
    with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''

# Get the classifiers from the classifiers file
tolines = lambda c: list(filter(None, map(lambda s: s.strip(), c.split('\n'))))
try:
    with open(path.join(here, 'classifiers.txt'), encoding='utf-8') as f:
        classifiers = tolines(f.read())
except:
    classifiers = []

version_ns = {}
try:
    execfile(path.join(here, 'medikit/_version.py'), version_ns)
except EnvironmentError:
    version = 'dev'
else:
    version = version_ns.get('__version__', 'dev')

setup(
    author='Romain Dorgueil',
    author_email='romain@dorgueil.net',
    description='Opinionated python 3.5+ project management.',
    license='Apache License, Version 2.0',
    name='medikit',
    python_requires='>=3.5',
    version=version,
    long_description=long_description,
    classifiers=classifiers,
    packages=find_packages(exclude=['ez_setup', 'example', 'test']),
    include_package_data=True,
    install_requires=[
        'git-semver ~= 0.2.0', 'jinja2 ~= 2.9', 'mondrian ~= 0.7',
        'packaging ~= 19.0', 'pip-tools ~= 3.0', 'stevedore ~= 1.28',
        'whistle ~= 1.0', 'yapf ~= 0.20'
    ],
    extras_require={
        'dev': [
            'coverage ~= 4.5', 'isort', 'pytest ~= 5.0', 'pytest-cov ~= 2.7',
            'releases >= 1.6, < 1.7', 'sphinx ~= 1.7', 'sphinx-sitemap ~= 1.0'
        ]
    },
    entry_points={
        'console_scripts': ['medikit=medikit.__main__:main'],
        'medikit.feature': [
            'django = medikit.feature.django:DjangoFeature',
            'docker = medikit.feature.docker:DockerFeature',
            'format = medikit.feature.format:FormatFeature',
            'git = medikit.feature.git:GitFeature',
            'kube = medikit.feature.kube:KubeFeature',
            'make = medikit.feature.make:MakeFeature',
            'nodejs = medikit.feature.nodejs:NodeJSFeature',
            'pylint = medikit.feature.pylint:PylintFeature',
            'pytest = medikit.feature.pytest:PytestFeature',
            'python = medikit.feature.python:PythonFeature',
            'sphinx = medikit.feature.sphinx:SphinxFeature',
            'webpack = medikit.feature.webpack:WebpackFeature',
            'yapf = medikit.feature.yapf:YapfFeature'
        ]
    },
    url='https://python-medikit.github.io/',
    download_url=
    'https://github.com/python-medikit/medikit/archive/{version}.tar.gz'.
    format(version=version),
)
