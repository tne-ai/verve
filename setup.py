from setuptools import setup, find_packages

setup(
    name="tne",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
    ],
    author="Lucas Hahn",
    author_email="lucas@tne.ai",
    description="TNE Python-authoring SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tne-ai/verve",  # Update this with your package's URL
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.11',  # Specify the Python versions you support
)
