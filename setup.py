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

setup(
    name='rollbar',
    packages=find_packages(),
    version=VERSION,
    entry_points= {
        'paste.filter_app_factory': [
            'pyramid=rollbar.contrib.pyramid:create_rollbar_middleware'
        ],
        'console_scripts': ['rollbar=rollbar.cli:main']
    },
    description='Logs exceptions and other data to Rollbar. Provides a generic interface, as well as a Django middleware and a Pyramid tween.',
    long_description=README,
    author='Rollbar, Inc.',
    author_email='support@rollbar.com',
    test_suite='rollbar.test',
    url='http://github.com/rollbar/pyrollbar',
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        ],
    install_requires=[
        'requests',
        ],
    tests_require=[
        'mock',
        'webob',
        'Flask',
        'blinker'
        ],
    )

