"""(c) Copyright 2015 Olli Wang. All Rights Reserved."""

import os
import sys

from distutils.core import setup


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join)
    in a platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, package_data = [], {}

root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
cclint_dir = 'cclint'

for dirpath, dirnames, filenames in os.walk(cclint_dir):
    # Ignore PEP 3147 cache dirs and those whose names start with '.'
    dirnames[:] = [d for d in dirnames if \
        not d.startswith('.') and d != '__pycache__']
    parts = fullsplit(dirpath)
    package_name = '.'.join(parts)
    if '__init__.py' in filenames:
        packages.append(package_name)
    elif filenames:
        relative_path = []
        while '.'.join(parts) not in packages:
            relative_path.append(parts.pop())
        relative_path.reverse()
        path = os.path.join(*relative_path)
        package_files = package_data.setdefault('.'.join(parts), [])
        package_files.extend([os.path.join(path, f) for f in filenames])

setup(
    name='cclint',
    version='0.1',
    description="An enhanced version of the Goggle's cpplint tool",
    author='Olli Wang',
    author_email='olliwang@ollix.com',
    url='https://github.com/olliwang/cclint',
    license='BSD',
    packages=packages,
    scripts=['cclint/bin/cclint'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Terminals',
    ]
)
