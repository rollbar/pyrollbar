<p align="center">
  <img alt="rollbar-logo" src="https://user-images.githubusercontent.com/3300063/207964480-54eda665-d6fe-4527-ba51-b0ab3f41f10b.png" />
</p>

<h1 align="center">Pyrollbar</h1>

<p align="center">
  <strong>Proactively discover, predict, and resolve errors in real-time with <a href="https://rollbar.com">Rollbar’s</a> error monitoring platform. <a href="https://rollbar.com/signup/">Start tracking errors today</a>!</strong>
</p>


![Build Status](https://github.com/rollbar/pyrollbar/workflows/Pyrollbar%20CI/badge.svg?tag=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rollbar)

Python notifier for reporting exceptions, errors, and log messages to [Rollbar](https://rollbar.com).

## Key benefits of using Pyrollbar are:
- **Frameworks:** Pyrollbar supports popular Python frameworks such as <a href="https://docs.rollbar.com/docs/django">Django</a>, <a href="https://docs.rollbar.com/docs/flask">Flask</a>, <a href="https://docs.rollbar.com/docs/fastapi">FastAPI</a>, <a href="https://docs.rollbar.com/docs/aws-lambda-1">AWS Lambda</a> and more!
- **Automatic error grouping:** Rollbar aggregates Occurrences caused by the same error into Items that represent application issues. <a href="https://docs.rollbar.com/docs/grouping-occurrences">Learn more about reducing log noise</a>.
- **Advanced search:** Filter items by many different properties. <a href="https://docs.rollbar.com/docs/search-items">Learn more about search</a>.
- **Customizable notifications:** Rollbar supports several messaging and incident management tools where your team can get notified about errors and important events by real-time alerts. <a href="https://docs.rollbar.com/docs/notifications">Learn more about Rollbar notifications</a>.

## Python Versions Supported

| PyRollbar Version | Python Version Compatibility                  | Support Level       |
|-------------------|-----------------------------------------------|---------------------|
| 1.1.0             | 3.6, 3.7. 3.8, 3.9, 3.10, 3.11, 3.12          | Full                |
| 0.16.3            | 2.7, 3.4, 3.5, 3.6, 3.7. 3.8, 3.9, 3.10, 3.11 | Security Fixes Only |

#### Support Level Definitions

**Full** - We will support new features of the library and test against all supported versions.

**Security Fixes Only** - We will only provide critical security fixes for the library.

## Frameworks Supported

Generally, PyRollbar can be used with any Python framework. However, we have official support for the following frameworks:

| Framework | Support Duration           | Tested Versions |
|-----------|----------------------------|-----------------|
| Celery    | Release +1 year            | None            |
| Django    | Release or LTS end +1 year | 3.2, 4.2, 5.0   |
| FastAPI   | Release +1 year            | 0.101, 0.112    |
| Flask     | Release +1 year            | 1.1, 2.3, 3.0   |
| Pyramid   | Release +1 year            | 1.10, 2.0       |

Official support means that we ship and maintain integrations for these frameworks. It also means that we test against these frameworks as part of our CI pipeline.

Generally, we will support the last year of releases for a framework. If a framework has a defined support period (including LTS releases), we will support the release for the duration of that period plus one year.

### Community Supported

There are also a number of community-supported integrations available. For more information, see the [Python SDK docs](https://docs.rollbar.com/docs/python-community-supported-sdks).

## Setup Instructions

1. [Sign up for a Rollbar account](https://rollbar.com/signup)
2. Follow the [Quick Start](https://docs.rollbar.com/docs/python#section-quick-start) instructions in our [Python SDK docs](https://docs.rollbar.com/docs/python) to install pyrollbar and configure it for your platform.

## Usage and Reference

For complete usage instructions and configuration reference, see our [Python SDK docs](https://docs.rollbar.com/docs/python).

## Release History & Changelog

See our [Releases](https://github.com/rollbar/pyrollbar/releases) page for a list of all releases, including changes.

## Help / Support

If you run into any issues, please email us at [support@rollbar.com](mailto:support@rollbar.com)

For bug reports, please [open an issue on GitHub](https://github.com/rollbar/pyrollbar/issues/new).


## Contributing

1. Fork it
2. Create your feature branch (```git checkout -b my-new-feature```).
3. Commit your changes (```git commit -am 'Added some feature'```)
4. Push to the branch (```git push origin my-new-feature```)
5. Create new Pull Request

Tests are in `rollbar/test`. To run the tests: `python setup.py test`
