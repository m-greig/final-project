# package_name

## Installation

This package is built with `setuptools`. To install, navigate to the root of the downloaded package (where the pyproject.toml file is) and execute:

`pip install .`

If you want to have an editable installation (e.g. for development):

`pip install . -e`

If you are planning on developing this package, it is recommended that you first create a new conda environment. Activate the new environment and install the package into that environment.

## Quick start

```python
import package_name as pn

pn.my_function() # Returns None
my_class = pn.MyClass()
```

## Python version

This package, in its current form, runs on Python versions from 3.7+