import importlib.resources as pkg_resources
import os

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from glob import glob

from auviewer import __VERSION__

NAME = 'auviewer'
VERSION = __VERSION__

# TODO(gus): Temp
VERSION = VERSION + '.2'

RECOMPILE_CYTHON = False

# Handle optional cython re-compilation (should be disabled by default for
# standard client build-installs)
ext = '.pyx' if RECOMPILE_CYTHON else '.c'
extensions = [Extension("auviewer.cylib", ["auviewer/cylib"+ext])]
if RECOMPILE_CYTHON:
    from Cython.Build import cythonize
    from numpy import get_include
    extensions = cythonize(extensions, language_level=3)

def read(fn):
    return open(os.path.join(os.path.dirname(__file__), fn)).read()

pkg_files = [elem.replace('auviewer/', '') for elem in glob('auviewer/static/**/*', recursive=True) if os.path.isfile(elem)]

# Workaround to import numpy without assuming it's initially installed.
# From https://stackoverflow.com/questions/19919905/how-to-bootstrap-numpy-installation-in-setup-py
class build_ext(_build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process:
        __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

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
    cmdclass={'build_ext':build_ext},
	ext_modules=extensions,
    package_data={NAME: pkg_files},
    install_requires=[
        'audata',
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
    packages=find_packages(),
    setup_requires=['numpy']
)
