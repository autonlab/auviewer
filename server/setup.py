import os
from distutils.core import setup
from Cython.Build import cythonize

setup(
	ext_modules=cythonize(os.environ['MEDVIEW_BASE_DIR']+"/server/*.pyx")
)
