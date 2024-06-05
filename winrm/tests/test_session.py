import pytest

from winrm import Session


def test_run_cmd(protocol_fake):
    # TODO this test should cover __init__ method
    s = Session("windows-host", auth=("john.smith", "secret"))
    s.protocol = protocol_fake

    r = s.run_cmd("ipconfig", ["/all"])

    assert r.status_code == 0
    assert b"Windows IP Configuration" in r.std_out
    assert len(r.std_err) == 0


def test_run_ps_with_error(protocol_fake):
    # TODO this test should cover __init__ method
    s = Session("windows-host", auth=("john.smith", "secret"))
    s.protocol = protocol_fake

    r = s.run_ps('Write-Error "Error"')

    assert r.status_code == 1
    assert b'Write-Error "Error"' in r.std_err
    assert len(r.std_out) == 0


def test_target_as_hostname():
    s = Session("windows-host", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host:5985/wsman"


def test_target_as_hostname_then_port():
    s = Session("windows-host:1111", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host:1111/wsman"


def test_target_as_schema_then_hostname():
    s = Session("http://windows-host", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host:5985/wsman"


def test_target_as_schema_then_hostname_then_port():
    s = Session("http://windows-host:1111", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host:1111/wsman"


def test_target_as_full_url():
    s = Session("http://windows-host:1111/wsman", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host:1111/wsman"


def test_target_with_dots():
    s = Session("windows-host.example.com", auth=("john.smith", "secret"))
    assert s.url == "http://windows-host.example.com:5985/wsman"


def test_decode_clixml_error():
    s = Session("windows-host.example.com", auth=("john.smith", "secret"))
    msg = b'#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"><Obj S="progress" RefId="0"><TN RefId="0"><T>System.Management.Automation.PSCustomObject</T><T>System.Object</T></TN><MS><I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil /><PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj><Obj S="progress" RefId="1"><TNRef RefId="0" /><MS><I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil /><PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj><S S="Error">fake : The term \'fake\' is not recognized as the name of a cmdlet, function, script file, or operable program. Check _x000D__x000A_</S><S S="Error">the spelling of the name, or if a path was included, verify that the path is correct and try again._x000D__x000A_</S><S S="Error">At line:1 char:1_x000D__x000A_</S><S S="Error">+ fake cmdlet_x000D__x000A_</S><S S="Error">+ ~~~~_x000D__x000A_</S><S S="Error">    + CategoryInfo          : ObjectNotFound: (fake:String) [], CommandNotFoundException_x000D__x000A_</S><S S="Error">    + FullyQualifiedErrorId : CommandNotFoundException_x000D__x000A_</S><S S="Error"> _x000D__x000A_</S></Objs>'
    expected = b"fake : The term 'fake' is not recognized as the name of a cmdlet, function, script file, or operable program. Check \nthe spelling of the name, or if a path was included, verify that the path is correct and try again.\nAt line:1 char:1\n+ fake cmdlet\n+ ~~~~\n    + CategoryInfo          : ObjectNotFound: (fake:String) [], CommandNotFoundException\n    + FullyQualifiedErrorId : CommandNotFoundException"
    actual = s._clean_error_msg(msg)
    assert actual == expected


def test_decode_clixml_no_clixml():
    s = Session("windows-host.example.com", auth=("john.smith", "secret"))
    msg = b"stderr line"
    expected = b"stderr line"
    actual = s._clean_error_msg(msg)
    assert actual == expected


def test_decode_clixml_no_errors():
    s = Session("windows-host.example.com", auth=("john.smith", "secret"))
    msg = b'#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"><Obj S="progress" RefId="0"><TN RefId="0"><T>System.Management.Automation.PSCustomObject</T><T>System.Object</T></TN><MS><I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil /><PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj><Obj S="progress" RefId="1"><TNRef RefId="0" /><MS><I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil /><PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj></Objs>'
    expected = msg
    actual = s._clean_error_msg(msg)
    assert actual == expected


def test_decode_clixml_invalid_xml():
    s = Session("windows-host.example.com", auth=("john.smith", "secret"))
    msg = b"#< CLIXML\r\n<in >dasf<?dsfij>"

    with pytest.warns(UserWarning, match="There was a problem converting the Powershell error message"):
        actual = s._clean_error_msg(msg)

    assert actual == msg
