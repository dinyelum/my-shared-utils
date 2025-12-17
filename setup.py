from setuptools import setup, find_packages

setup(
    name="my-shared-utils",
    version="1.0.1",
    # packages=find_packages(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # package_dir={'my_shared_utils': 'src/my_shared_utils'},
    # packages=['my_shared_utils'],
    install_requires=[
        # List your dependencies here
        "python-dotenv>=1.1.1",
        "mysql-connector-python>=9.4.0",
    ],
    # py_modules=[],  # No top-level modules
    author="Joe",
    description="Shared utilities for Python projects",
)
