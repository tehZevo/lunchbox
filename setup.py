from setuptools import setup, find_packages

setup(name="lunchbox",
    version="0.0.0",
    install_requires=[
        "mido",
        "python-rtmidi",
        "pyyaml"
    ],
    entry_points={"console_scripts": ["lunchbox=lunchbox.apps.controller:main"]},
    extras_require={
        "visualizer": ["pygame"],
    },
    packages=find_packages()
)
