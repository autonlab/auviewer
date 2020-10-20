from setuptools import setup, find_packages, Extension
import argparse
import os
from glob import glob

from auviewer import __VERSION__

NAME = 'auviewer'
VERSION = __VERSION__

RECOMPILE_CYTHON = False

ext = '.pyx' if RECOMPILE_CYTHON else '.c'
include_dirs = []
extensions = [Extension("auviewer.cylib", ["auviewer/cylib"+ext])]
if RECOMPILE_CYTHON:
    from Cython.Build import cythonize
    from numpy import get_include
    extensions = cythonize(extensions, language_level=3)
    include_dirs=[get_include()]

def read(fn):
    return open(os.path.join(os.path.dirname(__file__), fn)).read()

pkg_files = [elem.replace('auviewer/', '') for elem in glob('auviewer/static/**/*', recursive=True) if os.path.isfile(elem)]

setup(
    name=NAME,
    version=VERSION,
    description='A general-purpose time series exploration & annotation tool.',
    long_description='',
    author='Gus Welter',
    author_email='gwelter@cmu.edu',
    license='MIT',
    entry_points={
        'console_scripts': [
            'auv=auviewer.serve:main'
        ]
    },
	ext_modules=extensions,
    include_dirs=include_dirs,
    package_data={'auviewer': pkg_files},
    include_package_data=True,
    install_requires=[
        'audata',
        'cython',
        'email_validator',
        'flask',
        'flask-login',
        'flask-mail',
        'flask-socketio',
        'flask-sqlalchemy',
        'flask-wtf',
        'htmlmin',
        'jsbeautifier',
        'numpy',
        'pandas',
        'passlib',
        'psutil',
        'pycrypto',
        'python-socketio',
        'simplejson',
    ],
    packages=find_packages()
)
