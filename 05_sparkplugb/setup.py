from setuptools import setup, find_packages

setup(name="uns_sparkplugb",
      packages=find_packages(where="./src", exclude=("./tests")))
