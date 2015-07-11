#!/usr/bin/env python

from setuptools import setup

setup(
    name='Judgish',
    version='0.1',
    description='Analyze and judge the people you follow on Twitter',
    license='MIT',
    author='Kirk Strauser',
    author_email='kirk@strauser.com',
    url='https://github.com/kstrauser/judgish',
    package_dir={'': 'src'},
    py_modules=['judgish'],
    install_requires=[
        'textblob',
        'twitter',
        'PyYAML',
    ],
    entry_points={
        'console_scripts': [
            'judgish=judgish:main'
        ],
    },
)
