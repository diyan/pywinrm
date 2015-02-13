import mock
import sys
import os

from winrm import (
    cli,
    Response,
    Session
)

HERE = os.path.dirname(__file__)

def test_get_args():
    cmd = 'winrm -p password Administrator@0.0.0.0 hostname'
    sys.argv = cmd.split()

    args = cli.get_args()

    assert args.command == 'hostname'
    assert args.interpreter == 'cmd'
    assert args.login_name == 'Administrator'
    assert args.hostname == '0.0.0.0'

def test_get_args_ps():
    cmd = 'winrm -v -p password -v -i ps 0.0.0.0 1+1'
    sys.argv = cmd.split()
    args = cli.get_args()

    assert args.command == '1+1'
    assert args.interpreter == 'ps'
    assert args.verbose == True
    assert args.login_name == os.environ.get('USER')
    assert args.hostname == '0.0.0.0'

def test_ps_script_with_successful_response(capsys):
    cmd = 'winrm -v -p password -v -i ps --args 1 administrator@0.0.0.0'
    script = open(os.path.join(HERE, 'sample_script.ps1'))

    # stdout, stderr, return code
    response_args = '2', '', 0
    mock_response = Response(response_args)

    with mock.patch.object(Session, 'run_ps') as mock_method:
        mock_method.return_value = mock_response

        with mock.patch('sys.argv', cmd.split()):
            with mock.patch('sys.stdin', script):
                cli.main()

    mock_method.assert_called_with(u'1+1', ['1'])

    out, err = capsys.readouterr()
    assert out == '2'

def test_ps_with_erronous_response(capsys):
    cmd = 'winrm -v -p password -v -i ps administrator@0.0.0.0 ()'
    sys.argv = cmd.split()

    response_args = '', 'What a stupid command!', 1
    mock_response = Response(response_args)

    with mock.patch.object(Session, 'run_ps') as mock_method:
        mock_method.return_value = mock_response

        # cancel exit on the error
        with mock.patch('sys.exit'):
            cli.main()

    mock_method.assert_called_with(u'()', [])
    
    out, err = capsys.readouterr()
    assert err == 'What a stupid command!'
