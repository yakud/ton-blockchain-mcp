from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines()]

setup(
    name="ton-mcp-server",
    version="0.1.0",
    author="Devon Mojito",
    author_email="devonmojito@gmail.com",
    description="Model Context Protocol server for TON blockchain data analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/devonmojito/ton-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0", "mypy>=1.5.0"],
        "nlp": ["spacy>=3.6.0", "nltk>=3.8.0"],
    },
    entry_points={
        "console_scripts": [
            "ton-mcp-server=src.mcp_server:main",
        ],
    },
)