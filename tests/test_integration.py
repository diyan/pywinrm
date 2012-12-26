from nose import SkipTest
import re
from fixtures import real_winrm_service

class TestIntegration(object):
    @classmethod
    def setup_class(cls):
        cls.winrm = real_winrm_service()

    def teardown(self):
        pass

    def test_open_shell_and_close_shell(self):
        shell_id = self.winrm.open_shell()
        assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', shell_id)

        self.winrm.close_shell(shell_id)

    def test_run_command_with_arguments_and_cleanup_command(self):
        shell_id = self.winrm.open_shell()
        command_id = self.winrm.run_command(shell_id, 'ipconfig', ['/all'])
        assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

        self.winrm.cleanup_command(shell_id, command_id)
        self.winrm.close_shell(shell_id)

    def test_run_command_without_arguments_and_cleanup_command(self):
        shell_id = self.winrm.open_shell()
        command_id = self.winrm.run_command(shell_id, 'hostname')
        assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

        self.winrm.cleanup_command(shell_id, command_id)
        self.winrm.close_shell(shell_id)

    def test_get_command_output(self):
        shell_id = self.winrm.open_shell()
        command_id = self.winrm.run_command(shell_id, 'ipconfig', ['/all'])
        stdout, stderr, return_code = self.winrm.get_command_output(shell_id, command_id)
        assert return_code == 0
        assert 'Windows IP Configuration' in stdout
        assert len(stderr) == 0

        self.winrm.cleanup_command(shell_id, command_id)
        self.winrm.close_shell(shell_id)

    def test_set_timeout(self):
        raise SkipTest('Not implemented yet')

    def test_set_max_env_size(self):
        raise SkipTest('Not implemented yet')

    def test_set_locale(self):
        raise SkipTest('Not implemented yet')