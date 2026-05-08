"""
Setup script for EVENT_HORIZON — Defensive Authentication Resilience Framework (DARF)
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="event-horizon-darf",
    version="1.0.0",
    author="EVENT_HORIZON Team",
    author_email="event-horizon@example.com",
    description="Defensive Authentication Resilience Framework (DARF)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/event-horizon/darf",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "event-horizon=event_horizon.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "event_horizon": [
            "config/*.yaml",
            "config/*.json",
            "docs/*.md",
        ],
    },
    zip_safe=False,
)
