from setuptools import setup, find_packages

setup(
    name="my-shared-utils",
    version="3.0.0",
    # packages=find_packages(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # List your dependencies here
        "python-dotenv>=1.1.1",
        # "mysqlclient>=2.2.7"
        # "mysql-connector-python>=9.4.0",
    ],
    # py_modules=[],  # No top-level modules
    author="Joe",
    description="Shared utilities for Python projects",
)
# pipenv install git+https://github.com/dinyelum/my-shared-utils.git@v1.3.1
