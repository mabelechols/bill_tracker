from setuptools import setup, find_packages


with open("README.rst") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="bill",
    version="0.1.0",
    description="Bank statement reading utility",
    long_description=readme,
    author="Mabel echols",
    author_email="echols.mabel@gmail.com",
    url="https://github.com/mabelechols/bill_tracker",
    license=license,
    packages=find_packages(),
)
