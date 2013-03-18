# pgen2's setup.py

from distutils.core import setup

setup(
    name = "pgen2",
    packages = ["pgen2"],
    version = "0.1.0",
    description = "Pure Python implementation of pgen, the Python parser generator",
    author = "Jon Riehl",
    author_email = "jon.riehl@gmail.com",
    url = "https://github.com/mythonlang/pgen2/",
    keywords = ["parser", "parser generator"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operation System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
)
