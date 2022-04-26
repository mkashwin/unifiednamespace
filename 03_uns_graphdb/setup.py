from setuptools import setup, find_packages

setup(name="uns_graphdb",
      packages=find_packages(where="./src", exclude=("./tests")))
