from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
this_directory = pathlib.Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="algebraic_search",
    version="0.1.2",
    description="A Python library for algebraic search.",
    author="Alex Towell",
    author_email="lex@metafunctor.com",
    url="https://github.com/queelius/algebraic_search",  # GitHub or other repo URL
    package_dir={"": "src"},
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    install_requires=[
        # Add dependencies here, e.g., "numpy>=1.21.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
