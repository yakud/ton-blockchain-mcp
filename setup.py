from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

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
    install_requires=[
        "mcp[cli]>=1.4.1",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "ton",
        "aiohttp>=3.8.0",
        "httpx>=0.24.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "orjson>=3.9.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "structlog>=23.0.0",
        "python-dateutil>=2.8.0",
        "anyio>=3.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "nlp": [
            "spacy>=3.6.0",
            "nltk>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ton-mcp-server=src.mcp_server:main",
        ],
    },
)