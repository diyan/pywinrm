import os
import sys
import urllib
from distutils.core import Command, setup

__version__ = '0.0.2dev'
project_name = 'pywinrm'

# PyPi supports only reStructuredText, so pandoc should be installed
# before uploading package
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = ''


class BootstrapEnvironmentCommand(Command):
    description = 'create project development environment from scratch'
    user_options = []

    def __init__(self, dist):
        Command.__init__(self, dist)
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        self.temp_dir = os.path.join(self.project_dir, '~temp')
        self.virtualenv_dir = os.path.join(self.project_dir, 'env')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.setup_virtual_environment()

    def setup_virtual_environment(self):
        """Creates Python env if it not exists or re-create if outdated."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        if not os.path.exists(self.virtualenv_dir):
            virtualenv_setup_path = os.path.join(self.temp_dir, 'virtualenv.py')
            urllib.urlretrieve(
                'https://raw.github.com/pypa/virtualenv/master/virtualenv.py',
                virtualenv_setup_path)
            virtualenv_prompt = '\({0}\)'.format(project_name) \
                if os.name == 'posix' else '({0})'.format(project_name)
            os.system('python {0} --prompt={1} env'.format(
                virtualenv_setup_path, virtualenv_prompt))
            self.activate_virtual_environment()
            easy_install_setup_path = os.path.join(self.temp_dir, 'ez_setup.py')
            urllib.urlretrieve(
                'http://peak.telecommunity.com/dist/ez_setup.py',
                easy_install_setup_path)
            os.system(
                'python {0} -U setuptools'.format(easy_install_setup_path))
            os.system(
                'pip install -r requirements.txt --download-cache={0}'.format(
                    self.temp_dir))

    def activate_virtual_environment(self):
        """ Activates virtual environment in the same way as activate.bat or activate.sh from virtualenv package """
        if not hasattr(sys, 'real_prefix') or 'VIRTUAL_ENV' not in os.environ:
            activate_this = '{0}/env/bin/activate_this.py'.format(
                self.project_dir)
            virtual_env_path = '{0}/env/bin:'.format(self.project_dir)
            if os.name != 'posix':
                activate_this = '{0}/env/Scripts/activate_this.py'.format(
                    self.project_dir)
                virtual_env_path = '{0}\env\Scripts;'.format(self.project_dir)

            execfile(activate_this, dict(__file__=activate_this))
            path = os.environ['PATH']
            os.environ['PATH'] = virtual_env_path + path


setup(name=project_name,
      version=__version__,
      description='Python library for Windows Remote Management',
      long_description=long_description,
      keywords='winrm ws-man devops ws-management'.split(' '),
      author='Alexey Diyan',
      author_email='alexey.diyan@gmail.com',
      url='http://github.com/diyan/pywinrm/',
      license='MIT license',
      packages=['winrm', 'winrm.tests'],
      package_data={'winrm.tests': ['config_example.json', '*.ps1']},
      install_requires=['xmlwitch', 'isodate'],
      dependency_links=[
          'https://github.com/diyan/xmlwitch/tarball/master#egg=xmlwitch-dev'],
      cmdclass={
          'bootstrap_env': BootstrapEnvironmentCommand}
)
