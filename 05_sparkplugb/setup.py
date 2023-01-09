from setuptools import setup, find_packages

setup(name="uns_spb_mapper",
      packages=find_packages(where="./src", exclude=("./tests")))
