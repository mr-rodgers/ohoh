# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

def read(relpath):
    with open(path.join(here, relpath), encoding="utf-8") as f:
        return f.read()

requires = ["server-reloader"]

if sys.version_info < (2, 7):
    requires.append("argparse")
    requires.append("importlib")

if (3, ) <= sys.version_info < (3, 2):
    requires.append("argparse")

if (3, ) <= sys.version_info < (3, 1):
    requires.append("importlib")


setup(
    name='ohoh',
    version="0.0.0",

    description='A debug server for WSGI apps.',
    long_description=read("README.rst"),

    url='https://github.com/te-je/ohoh',

    author='Te-je Rodgers',
    author_email='tjd.rodgers@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Environment :: Console',
        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',

        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    ],

    keywords='findig wsgi debug server',

    setup_requires=['setuptools_scm'],
    use_scm_version={"write_to": "ohoh/VERSION.txt"},

    packages=find_packages(exclude=['tests']),
    install_requires=requires,

    extras_require={

    },

    package_data={
        'ohoh': ['VERSION.txt'],
    },

    entry_points={
        'console_scripts': [
            "ohoh=ohoh:main",
        ],
    },

    use_2to3=True,
)
