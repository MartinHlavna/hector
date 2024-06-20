from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Hector',
    ext_modules=cythonize("hector.py"),
)
