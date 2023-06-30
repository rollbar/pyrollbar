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
    'httpx',
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
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
        'requests>=0.12.1',
    ],
    tests_require=tests_require,
)
