import os
from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(
	ext_modules=cythonize(os.environ['MEDVIEW_BASE_DIR']+"/server/*.pyx"),
	include_dirs=[numpy.get_include()]
)
