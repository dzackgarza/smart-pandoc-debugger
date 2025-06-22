from setuptools import setup, find_packages

setup(
    name="smart-pandoc-debugger",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "spd=smart_pandoc_debugger.cli:main",
        ],
    },
)
