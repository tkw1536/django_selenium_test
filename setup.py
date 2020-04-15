#!/usr/bin/env python

# read the contents of your README file
from os import path

from setuptools import find_packages, setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
    ],
    name="django-selenium-test",
    version="1.0.2",
    license="BSD 3-Clause License",
    description="Write clean Selenium tests in Django",
    author="Tom Wiesing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email="tkw01536@gmail.com",
    url="https://github.com/tkw1536/django_selenium_test",
    packages=find_packages(),
    install_requires=["django>=2.0,<3.1", "selenium>=2.40,<4"],
    test_suite="tests.tests",
)
