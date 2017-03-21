from setuptools import setup

__version__ = '1.0.0'
project_name = 'pywinrm'

# PyPi supports only reStructuredText, so pandoc should be installed
# before uploading package
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = ''

install_requires = ['xmltodict', 'requests>=2.9.1', 'requests_ntlm>=0.3.0', 'six']
try:
    from collections import OrderedDict
except ImportError:
    install_requires.append('ordereddict')

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
    packages=('winrm', 'tests'),
    package_data={'tests': ['*.ps1']},
    install_requires=install_requires,
    extras_require = dict(kerberos=['requests-kerberos>=0.10.0'], credssp=['requests-credssp>=0.0.1']),
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration'
    ],
)
