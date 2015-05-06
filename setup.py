from setuptools import setup, find_packages

setup(
    name = 'projexui',
    version = '3.0.5',
    author = 'Eric Hulser',
    author_email = 'eric.hulser@gmail.com',
    maintainer = 'Eric Hulser',
    maintainer_email = 'eric.hulser@gmail.com',
    description = 'Library of Qt extension widgets.',
    license = 'LGPL',
    keywords = '',
    url = 'https://github.com/ProjexSoftware/projexui',
    include_package_data=True,
    packages = find_packages(),
    install_requires = [
        'projex',
        'xqt'
    ],
    tests_require = [],
    long_description= 'Library of Qt extension widgets.',
    classifiers=[],
)