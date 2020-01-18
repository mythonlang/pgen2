# pgen2's setup.py

import setuptools

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pgen2",
    packages = ["pgen2"],
    version = "0.1.1",
    description = "Pure Python implementation of pgen, the Python parser "
    "generator",
    long_description = long_description,
    long_description_content_type="text/markdown",
    author = "Jon Riehl",
    author_email = "jon.riehl@gmail.com",
    url = "https://github.com/mythonlang/pgen2/",
    keywords = ["parser", "generator"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
)
