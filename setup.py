from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='bbar',
    version='0.1',
    description='bbar, the Batch Benchmark Automatic Runner',
    long_description=readme(),
    url='http://github.com/oj-lappi/bbar',
    author='Oskar Lappi',
    author_email='oskar.lappi@abo.fi',
    license='MIT',
    packages=['bbar'],
    install_requires=['toml'],
    entry_points={'console_scripts':['bbar=bbar.cmd:main']},
    zip_safe=False)
