from setuptools import setup, find_packages

setup(name="uns_mqtt",
      packages=find_packages(where="./src", exclude=("./tests")))
