"""Setup."""
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='tap-paypal',
    version='0.1.0',
    description='Singer.io tap for extracting data from PayPal',
    author='Yoast',
    url='https://yoast.com',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_paypal'],
    install_requires=[
        'httpx>=0.16.1',
        'python-dateutil>=2.8.1',
        'singer-python>=5.10.0',
    ],
    entry_points='''
        [console_scripts]
        tap-paypal=tap_paypal:main
    ''',
    packages=find_packages(),
    package_data={
        'tap_paypal': [
            'schemas/*.json'
        ]
    },
    include_package_data=True,
)
