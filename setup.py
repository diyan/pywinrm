import os

from setuptools import setup

__version__ = '0.3.1.dev0'
project_name = 'pywinrm'

# PyPi supports only reStructuredText, so pandoc should be installed
# before uploading package
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = ''


def install_deps():
    default = open('requirements.txt', 'r').readlines()
    pkg_list = []
    for resource in default:
        pkg_list.append(resource.strip())
    return pkg_list


def install_extras():
    extras = dict()
    for filename in os.listdir('requirements/extras'):
        extra_key = filename.replace('requirements/extras/requirements-', '').replace('.txt', '')
        extras[extra_key] = list()
        with open(filename, 'r') as req_file:
            for pkg_name in req_file.readlines():
                extras[extra_key].append(pkg_name)
    return extras


req_deps_list = install_deps()
extras_deps = install_extras()

setup(
    name=project_name,
    version=__version__,
    description='Python library for Windows Remote Management',
    long_description=long_description,
    keywords='winrm ws-man devops ws-management'.split(' '),
    author='Alexey Diyan',
    author_email='alexey.diyan@gmail.com',
    url='http://github.com/diyan/pywinrm/',
    license='MIT license',
    packages=('winrm', 'winrm.tests', 'winrm.vendor.requests_kerberos'),
    package_data={'winrm.tests': ['*.ps1']},
    install_requires=req_deps_list,
    extras_require=extras_deps,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration'
    ],
)
