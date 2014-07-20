import os
from setuptools import setup, find_packages
import projexui

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md')) as f:
        README = f.read()
except IOError:
    README = projexui.__doc__

try:
    VERSION = projexui.__version__
except AttributeError:
    VERSION = '1.0'

try:
    REQUIREMENTS = projexui.__depends__
except AttributeError:
    REQUIREMENTS = []

setup(
    name = 'projexui',
    version = VERSION,
    author = 'Projex Software',
    author_email = 'team@projexsoftware.com',
    maintainer = 'Projex Software',
    maintainer_email = 'team@projexsoftware.com',
    description = '''''',
    license = 'LGPL',
    keywords = '',
    url = 'http://www.projexsoftware.com',
    include_package_data=True,
    packages = find_packages(),
    install_requires = REQUIREMENTS,
    tests_require = REQUIREMENTS,
    long_description= README,
    classifiers=[],
)