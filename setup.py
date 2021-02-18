import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "python-daikin-altherma",
    version = "0.0.4",
    author = "Frank Villaro-Dixon",
    author_email = "frank@villaro-dixon.eu",
    description = ("Connect to daikin altherma heat pumps"),
    license = "MIT",
    keywords = "daikin altherma heat pump",
    url = "http://github.com/Frankkkkk/python-daikin-altherma",
    packages=['daikin_altherma'],
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    install_requires=['websocket-client', 'dpath'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
