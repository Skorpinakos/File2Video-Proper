from setuptools import setup
from Cython.Build import cythonize
import numpy as numpy


setup(
    ext_modules=cythonize(
        "app_extension.pyx", compiler_directives={"language_level": "3"}
    ),include_dirs=[numpy.get_include()]
)

# to supress warning https://stackoverflow.com/questions/52749662/using-deprecated-numpy-api