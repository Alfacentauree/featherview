#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="featherview",
    version="1.0.0",
    description="Ultra-lightweight, blazing-fast image viewer for Linux desktop",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="FeatherView Developers",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "featherview": ["*.css"],
    },
    entry_points={
        "console_scripts": [
            "featherview=featherview.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Graphics :: Viewers",
    ],
    python_requires=">=3.8",
)
