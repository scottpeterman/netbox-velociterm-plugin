from setuptools import setup, find_packages

setup(
    name='netbox-deviceterm',
    version='0.1.0',
    description='NetBox plugin to embed VelociTerm SSH terminal for devices',
    author='Scott Peterman',
    license='Apache 2.0',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
