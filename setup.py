from setuptools import setup, find_packages

setup(name="lunchbox",
  version="0.0.0",
  install_requires = [
    "mido",
    "python-rtmidi",
  ],
  packages=find_packages())