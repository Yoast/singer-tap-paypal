"""Setup."""
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='tap-paypal',
    version='0.1.0',
    description='Singer.io tap for extracting data from PayPal',
    author='Yoast',
    url='https://github.com/Yoast/singer-tap-paypal',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_paypal'],
    install_requires=[
        'httpx[http2]~=0.16.1',
        'python-dateutil~=2.8.1',
        'singer-python~=5.10.0',
    ],
    entry_points="""
        [console_scripts]
        tap-paypal=tap_paypal:main
    """,
    packages=find_packages(),
    package_data={
        'tap_paypal': [
            'schemas/*.json',
        ],
    },
    include_package_data=True,
)
