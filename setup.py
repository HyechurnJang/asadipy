import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='asadipy',
    version='0.1.1',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/asadipy',
    description='ASA Developing Interface for PYthon',
    long_description=read('README'),
    packages=['asadipy'],
    install_requires=['requests']
)
