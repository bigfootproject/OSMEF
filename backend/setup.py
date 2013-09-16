from setuptools import setup, find_packages

setup(
    name = "OSMeF",
    version = "0.1",
    packages = find_packages(),
    scripts = ['osmef.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['spur'],

    package_data = {
            # If any package contains *.txt or *.rst files, include them:
#            '': ['*.txt', '*.rst'],
            # And include any *.msg files found in the 'hello' package, too:
#            'hello': ['*.msg'],
        },

    # metadata for upload to PyPI
    author = "Daniele Venzano",
    author_email = "venza@brownhat.org",
    description = "OpenStack Measurement Framework",
    license = "Apache 2.0",
    keywords = "openstack measurement networking virtualization",
    url = "http://www.bigfootproject.eu",   # project home page, if any
    download_url = "https://github.com/bigfootproject/OSMEF",
    test_suite='tests',
    setup_requires=['nose>=1.0', 'coverage'],
    # could also include long_description, download_url, classifiers, etc.
)

