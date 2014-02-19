# -*- coding: utf-8 -*-

"""
Flask-Mime
----------

Provides MIME type based request dispatching mechanism to applications.
"""

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='Flask-Mime',
    version='0.1.0',
    url='https://github.com/lanius/flask-mime/',
    license='BSD',
    author='lanius',
    author_email='lanius@nirvake.org',
    description='Provides MIME type based request dispatching mechanism.',
    long_description=__doc__,
    py_modules=['flask_mime'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['Flask'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    tests_require=['tox'],
    cmdclass={'test': Tox}
)
