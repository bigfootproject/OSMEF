from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import sys

import osmef


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name="OSMeF",
    version=osmef.__version__,
    url="https://github.com/bigfootproject/OSMEF",
    license='Apache Software License 2.0',
    author="Daniele Venzano",
    author_email="venza@brownhat.org",
    description="OpenStack Measurement Framework",
    keywords="openstack measurement networking virtualization",
    download_url="https://github.com/bigfootproject/OSMEF",
    # could also include long_description, classifiers, etc.

    packages=['osmef'],
    include_package_data=True,
    scripts=['osmef.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=[],

    package_data={
            # If any package contains *.txt or *.rst files, include them:
            # '': ['*.txt', '*.rst'],
            # And include any *.msg files found in the 'hello' package, too:
            # 'hello': ['*.msg'],
    },

    # tests
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    test_suite='osmef.test'

)

