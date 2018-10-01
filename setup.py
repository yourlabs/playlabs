import pip
from setuptools import setup, find_packages, Command
import os, sys
from subprocess import Popen, PIPE
import shutil

with open('requirements.txt') as reqs_file:
    install_reqs = reqs_file.readlines()

process = subprocess.Popen(["pkg-config", "--variable=completionsdir", "bash-completion"], stdout=PIPE)
(output, err) = process.communicate()
exit_code = process.wait()

if not exit_code:
    shutil.copyfile('bash-completion.sh', f'{output}/playlabs.sh')

setup(
    name='playlabs',
    version=os.getenv('PLAYLABS_VERSION', 'dev'),
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
