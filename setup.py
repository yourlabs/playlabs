import pip
from setuptools import setup, find_packages, Command
import os, sys
from subprocess import Popen, PIPE
import shutil

with open('requirements.txt') as reqs_file:
    install_reqs = reqs_file.readlines()

home_path = os.getenv('HOME')
bashcompletion_dir = home_path
for d in ['.local', 'share', 'bash-completion', 'completions']:
    bashcompletion_dir = os.path.join(bashcompletion_dir, d)
    if not os.path.exists(bashcompletion_dir):
        os.mkdir(bashcompletion_dir)

bashcompletion_path = os.path.join(bashcompletion_dir, 'playlabs')
shutil.copyfile('bash-completion.sh', bashcompletion_path)

setup(
    name='playlabs',
    version=os.getenv('CI_COMMIT_REF_NAME', 'dev'),
    description='The obscene ansible paas distribution',
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/playlabs',
    packages=['playlabs'],
    include_package_data=True,
    license='MIT',
    install_requires=install_reqs,
    entry_points={
        'console_scripts': [
            'playlabs = playlabs.cli.main:cli',
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
