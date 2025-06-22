#!/usr/bin/env python3
"""
Setup script for Vibethon - Automatic Python Debugger
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
long_description = """
# Vibethon - Automatic Python Debugger

Vibethon is an enhanced Python debugger that automatically instruments your code to provide interactive debugging capabilities whenever errors occur.

## Features

- **Automatic function instrumentation**: All functions are automatically wrapped with error handling
- **Interactive REPL**: When errors occur, you get an interactive debugging session
- **Runtime instrumentation**: Functions are instrumented as they're imported/defined
- **Continue execution**: You can fix issues and continue execution from the error point
- **Compatible with existing Python code**: Works transparently with any Python script

## Usage

```bash
# Run a Python script with automatic debugging
vibethon script.py

# Run with arguments
vibethon script.py arg1 arg2

# Run a module
vibethon -m mymodule

# Run code directly
vibethon -c "print('Hello, World!')"
```

## Interactive Debugging

When an error occurs, you'll enter an interactive debugging session where you can:
- Inspect variables: `print(my_variable)`
- Modify variables: `my_variable = new_value`
- Run any Python code to understand the problem
- Continue execution: `continue` or `continue some_value`
- Exit the debugger: `quit` or `exit`
"""

setup(
    name="vibethon",
    version="1.0.1",
    description="Automatic Python Debugger with Interactive REPL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lev Chizhov, Guillermo Valle Perez, Joshua Harry",
    author_email="lc@lev.la",
    url="https://github.com/ennucore/vibethon",
    packages=find_packages(),
    py_modules=["vibethon_cli"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
    ],
    entry_points={
        "console_scripts": [
            "vibethon=vibethon_cli:main",
        ],
    },
    install_requires=[
        "openai>=1.0.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
        ],
    },
    keywords="debugger debug repl automatic instrumentation python error-handling",
    project_urls={
        "Bug Reports": "https://github.com/ennucore/vibethon/issues",
        "Source": "https://github.com/ennucore/vibethon",
        "Documentation": "https://github.com/ennucore/vibethon/blob/main/README.md",
    },
) 