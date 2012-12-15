import os, sys, urllib
from distutils.core import Command, setup

project_name = 'pywinrm'

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
        """Creates Python virtual environment if it not exists or re-create if outdated."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        if not os.path.exists(self.virtualenv_dir):
            virtualenv_setup_path = os.path.join(self.temp_dir, 'virtualenv.py')
            urllib.urlretrieve('https://raw.github.com/pypa/virtualenv/master/virtualenv.py', virtualenv_setup_path)
            virtualenv_prompt = '\({0}\)'.format(project_name) if os.name == 'posix' else '({0})'.format(project_name)
            os.system('python {0} --prompt={1} env'.format(virtualenv_setup_path, virtualenv_prompt))
            self.activate_virtual_environment()
            easy_install_setup_path = os.path.join(self.temp_dir, 'ez_setup.py')
            urllib.urlretrieve('http://peak.telecommunity.com/dist/ez_setup.py', easy_install_setup_path)
            os.system('python {0} -U setuptools'.format(easy_install_setup_path))
            os.system('pip install --requirement=requirements.txt --download-cache={0}'.format(self.temp_dir))

    def activate_virtual_environment(self):
        """ Activates virtual environment in the same way as activate.bat or activate.sh from virtualenv package """
        if not hasattr(sys, 'real_prefix') or 'VIRTUAL_ENV' not in os.environ:
            activate_this = '{0}/env/bin/activate_this.py'.format(self.project_dir)
            virtual_env_path = '{0}/env/bin:'.format(self.project_dir)
            if os.name != 'posix':
                activate_this = '{0}/env/Scripts/activate_this.py'.format(self.project_dir)
                virtual_env_path = '{0}\env\Scripts;'.format(self.project_dir)

            execfile(activate_this, dict(__file__=activate_this))
            path = os.environ['PATH']
            os.environ['PATH'] = virtual_env_path + path

setup(name=project_name,
    version='0.0.1',
    description='Python library for Windows Remote Management',
    author='Alexey Diyan',
    author_email='alexey.diyan@gmail.com',
    url='http://github.com/diyan/pywinrm/',
    packages=['distutils', 'distutils.command'],
    cmdclass={
        'bootstrap_env': BootstrapEnvironmentCommand  }
)