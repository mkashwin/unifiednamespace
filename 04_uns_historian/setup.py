from setuptools import setup, find_packages

setup(name="uns_historian",
      packages=find_packages(where="./src", exclude=("./tests")))
