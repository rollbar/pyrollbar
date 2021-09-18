import re
import os.path
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

README_PATH = os.path.join(HERE, 'README.md')
try:
    with open(README_PATH) as fd:
        README = fd.read()
except IOError:
    README = ''

INIT_PATH = os.path.join(HERE, 'rollbar/__init__.py')
with open(INIT_PATH) as fd:
    INIT_DATA = fd.read()
    VERSION = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", INIT_DATA, re.MULTILINE).group(1)

tests_require = [
    'webob',
    'blinker',
    'unittest2',
    'mock<=3.0.5; python_version < "3.3"',
    'enum34; python_version < "3.4"',
    'httpx; python_version >= "3.6"',
    'aiocontextvars; python_version == "3.6"'
]

setup(
    name='rollbar',
    packages=find_packages(),
    version=VERSION,
    entry_points={
        'paste.filter_app_factory': [
            'pyramid=rollbar.contrib.pyramid:create_rollbar_middleware'
        ],
        'console_scripts': ['rollbar=rollbar.cli:main']
    },
    description='Easy and powerful exception tracking with Rollbar. Send '
                'messages and exceptions with arbitrary context, get back '
                'aggregates, and debug production issues quickly.',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Rollbar, Inc.',
    author_email='support@rollbar.com',
    test_suite='rollbar.test.discover',
    url='http://github.com/rollbar/pyrollbar',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Framework :: Bottle",
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: Pylons",
        "Framework :: Pyramid",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        ],
    install_requires=[
        # The currently used version of `setuptools` has a bug,
        # so the version requirements are not properly respected.
        #
        # In the current version, `requests>= 0.12.1`
        # always installs the latest version of the package.
        'requests>=0.12.1; python_version == "2.7"',
        'requests>=0.12.1; python_version >= "3.6"',
        'requests<2.26,>=0.12.1; python_version == "3.5"',
        'requests<2.22,>=0.12.1; python_version == "3.4"',
        'requests<2.19,>=0.12.1; python_version == "3.3"',
        'requests<1.2,>=0.12.1; python_version == "3.2"',
        'requests<1.2,>=0.12.1; python_version == "3.1"',
        'requests<1.2,>=0.12.1; python_version == "3.0"',
        'six>=1.9.0'
    ],
    tests_require=tests_require,
)
