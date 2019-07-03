import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="biblionet",
    version="0.0.1",
    author="Henry Williams",
    author_email="htw2116@columbia.edu",
    description="A package for building networks from bibliographic metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/humford/EdLabResearch",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=False,
    data_files=[
        ("etc", ["biblionet/config.yaml"])
    ]
)