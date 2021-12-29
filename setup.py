# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in production_scheduling_shrdc/__init__.py
from production_scheduling_shrdc import __version__ as version

setup(
	name="production_scheduling_shrdc",
	version=version,
	description="This is a production scheduling app.",
	author="DCKY",
	author_email="dchu0011@student.monash.edu",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
