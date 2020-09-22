from setuptools import setup, find_packages
import numpy as np
import os
from glob import glob
from Cython.Build import cythonize

from auviewer import __VERSION__

NAME = 'auviewer'
VERSION = __VERSION__


def read(fn):
    return open(os.path.join(os.path.dirname(__file__), fn)).read()


pkg_files = []
for elem in glob('auviewer/static/**/*', recursive=True):
    if os.path.isfile(elem): pkg_files.append(elem.replace('auviewer/', ''))

setup(
    name=NAME,
    version=VERSION,
    description='A general-purpous time series exploration tool.',
    long_description=read('README.md'),
    author='Gus Welter',
    author_email='gwelter@cmu.edu',
    license='GNU LGPL 3',
    entry_points={
        'console_scripts': [
            'auviewer=auviewer.server.serve:main',

            'auv-clean=auviewer.tools.clean:main',
            'auv-generate-json-templates=auviewer.tools.generate_json_templates:main',
            'auv-realtime-client=auviewer.tools.rtclient:main',
            'auv-use-as-module=auviewer.tools.use_as_module:main',
            'auv-watch-realtime-files=auviewer.tools.watch_realtime_files:main'
        ]
    },
	ext_modules=cythonize('auviewer/server/*.pyx', language_level=3),
    include_dirs=[np.get_include()],
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
        'watchdog',

    ],
    packages=find_packages()
)
