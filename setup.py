import pip
from setuptools import setup, find_packages, Command
import os, sys

setup(
    name='playlabs',
    version='0.0.0',
    description='A distribution of ansible playbooks',
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://github.com/betagouv/mrs',
    packages=['playlabs'],
    include_package_data=True,
    license='MIT',
    install_requires=[
        'ansible',
        'click',
        'sh',
    ],
    entry_points={
        'console_scripts': [
            'playlabs = playlabs.main:cli',
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
