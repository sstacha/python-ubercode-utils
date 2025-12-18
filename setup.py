import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='python_ubercode_utils',
      version='2.0.3',
      description='Core python utilities for all apps',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/sstacha/python-ubercode-utils',
      author='Steve Stacha',
      author_email='sstacha@gmail.com',
      license='MIT',
      packages=setuptools.find_packages(exclude=["test"]),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
      ],
      python_requires='>=3.8',
      install_requires=[
      ],
)
