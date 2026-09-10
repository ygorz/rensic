#!/usr/bin/env python
"""Python project setup script."""

import os
from setuptools import find_packages, setup

setup(
    name=os.environ["PKG_NAME"],
    version=os.environ["PKG_VERSION"],
    description="Python data transformation project",
    author="Rensic",
    packages=find_packages(exclude=["contrib", "docs", "test"]),
    # Please specify your dependencies in conda_recipe/meta.yaml instead.
    install_requires=[],
    include_package_data=True,
    package_data={"myproject": ["data/*.csv", "data/*.md"]},
    entry_points={"transforms.pipelines": ["root = myproject.pipeline:my_pipeline"]},
)
