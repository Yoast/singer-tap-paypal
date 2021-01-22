#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-paypal",
    version="0.1.0",
    description="Singer.io tap for extracting data from PayPal",
    author="Yoast",
    url="https://yoast.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_paypal"],
    install_requires=[
        "singer-python",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-paypal=tap_paypal:main
    """,
    packages=["tap_paypal"],
    package_data = {
        "schemas": ["tap_paypal/schemas/*.json"]
    },
    include_package_data=True,
)
