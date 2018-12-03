import pip
from setuptools import setup, find_packages, Command
import os, sys
from subprocess import Popen, PIPE
import shutil


setup(
    name='playlab',
    setup_requires='setupmeta',
    versioning='dev',
    description='The obscene ansible distribution',
    author='James Pic, Thomas Mignot',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/playlab',
    include_package_data=True,
    license='MIT',
    entry_points={
        'console_scripts': [
            'playlab = clitoo:console_script',
        ],
        'playlab': [
            'playlab role = playlab:role',
            'playlab play = playlab:play',
        ],
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
