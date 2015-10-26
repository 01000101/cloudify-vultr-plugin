'''Description & dependencies for the Cloudify Vultr provider plugin'''

from setuptools import setup

setup(
    name='cloudify-vultr-plugin',
    author='Joshua Cornutt',
    author_email='jcornutt@gmail.com',

    version='1.3a7',
    description='Cloudify plugin for Vultr cloud infrastructure.',

    packages=['plugin'],

    license='MIT',
    install_requires=[
        'cloudify-plugins-common>=3.2.1',
        'vultr>=0.1.0'
    ]
)
