from unittest import mock

import pytest

from winrm import transport
from winrm.exceptions import InvalidCredentialsError, WinRMError


@pytest.fixture(scope="function", autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(transport, "DISPLAYED_CA_TRUST_WARNING", False)
    monkeypatch.setattr(transport, "DISPLAYED_PROXY_WARNING", False)

    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("TRAVIS_APT_PROXY", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)


def test_build_session_verify_default_no_env():
    t_default = transport.Transport(
        endpoint="https://example.com",
        username="test",
        password="test",
        auth_method="basic",
    )
    t_default.build_session()
    assert t_default.session.verify


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_default_from_env(env_var, monkeypatch):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        username="test",
        password="test",
        auth_method="basic",
    )
    with pytest.deprecated_call(match="'pywinrm' will use an environment variable defined CA Trust\\."):
        t_default.build_session()
    assert f"path_to_{env_var}" == t_default.session.verify


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_validate_from_env(env_var, monkeypatch):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
    )
    with pytest.deprecated_call(match="'pywinrm' will use an environment variable defined CA Trust\\."):
        t_default.build_session()
    assert f"path_to_{env_var}" == t_default.session.verify


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_explicit_with_env_var(env_var, monkeypatch, recwarn):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
        ca_trust_path="overridepath",
    )

    t_default.build_session()
    assert len(recwarn) == 0
    assert "overridepath" == t_default.session.verify


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_none_with_env_var(env_var, monkeypatch, recwarn):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
        ca_trust_path=None,
    )
    t_default.build_session()
    assert len(recwarn) == 0
    assert t_default.session.verify is True


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_ignore_with_env_var(env_var, monkeypatch, recwarn):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="ignore",
        username="test",
        password="test",
        auth_method="basic",
    )
    t_default.build_session()
    assert len(recwarn) == 0
    assert t_default.session.verify is False


@pytest.mark.parametrize("env_var", ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"])
def test_build_session_verify_ignore_bogus_path_and_with_env_var(env_var, monkeypatch, recwarn):
    monkeypatch.setenv(env_var, f"path_to_{env_var}")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="ignore",
        username="test",
        password="test",
        auth_method="basic",
        ca_trust_path="boguspath",
    )
    t_default.build_session()
    assert len(recwarn) == 0
    assert t_default.session.verify is False


def test_build_session_proxy_none_with_env_var(monkeypatch, recwarn):
    monkeypatch.setenv("HTTP_PROXY", "random_proxy")
    monkeypatch.setenv("HTTPS_PROXY", "random_proxy_2")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
        proxy=None,
    )

    t_default.build_session()
    assert len(recwarn) == 0
    assert {"no_proxy": "*"} == t_default.session.proxies


def test_build_session_proxy_explicit_value_no_env(recwarn):
    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
        proxy="test_proxy",
    )

    t_default.build_session()
    assert len(recwarn) == 0
    assert {"http": "test_proxy", "https": "test_proxy"} == t_default.session.proxies


def test_build_session_proxy_explicit_value_with_env(monkeypatch, recwarn):
    monkeypatch.setenv("HTTPS_PROXY", "random_proxy")

    t_default = transport.Transport(
        endpoint="https://example.com", server_cert_validation="validate", username="test", password="test", auth_method="basic", proxy="test_proxy"
    )

    t_default.build_session()
    assert len(recwarn) == 0
    assert {"http": "test_proxy", "https": "test_proxy"} == t_default.session.proxies


def test_build_session_proxy_with_env_https(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "random_proxy")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
    )

    with pytest.deprecated_call(match="'pywinrm' will use an environment defined proxy\\."):
        t_default.build_session()
    assert {"https": "random_proxy"} == t_default.session.proxies


def test_build_session_proxy_with_env_http(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "random_proxy")

    t_default = transport.Transport(
        endpoint="https://example.com",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="basic",
    )

    with pytest.deprecated_call(match="'pywinrm' will use an environment defined proxy\\."):
        t_default.build_session()
    assert {"http": "random_proxy"} == t_default.session.proxies


def test_build_session_server_cert_validation_invalid():
    with pytest.raises(WinRMError) as exc:
        transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="invalid_value",
            username="test",
            password="test",
            auth_method="basic",
        )
    assert "invalid server_cert_validation mode: invalid_value" == str(exc.value)


def test_build_session_krb_delegation_as_str():
    winrm_transport = transport.Transport(
        endpoint="Endpoint", server_cert_validation="validate", username="test", password="test", auth_method="kerberos", kerberos_delegation="True"
    )
    winrm_transport.kerberos_delegation is True


def test_build_session_krb_delegation_as_invalid_str():
    with pytest.raises(ValueError) as exc:
        transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="kerberos",
            kerberos_delegation="invalid_value",
        )
    assert "invalid truth value 'invalid_value'" == str(exc.value)


def test_build_session_no_username():
    with pytest.raises(InvalidCredentialsError) as exc:
        transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="validate",
            password="test",
            auth_method="basic",
        )
    assert "auth method basic requires a username" == str(exc.value)


def test_build_session_no_password():
    with pytest.raises(InvalidCredentialsError) as exc:
        transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="validate",
            username="test",
            auth_method="basic",
        )
    assert "auth method basic requires a password" == str(exc.value)


def test_build_session_invalid_auth():
    winrm_transport = transport.Transport(
        endpoint="Endpoint",
        server_cert_validation="validate",
        username="test",
        password="test",
        auth_method="invalid_value",
    )

    with pytest.raises(WinRMError) as exc:
        winrm_transport.build_session()
    assert "unsupported auth method: invalid_value" == str(exc.value)


def test_build_session_invalid_encryption():

    with pytest.raises(WinRMError) as exc:
        transport.Transport(
            endpoint="Endpoint",
            server_cert_validation="validate",
            username="test",
            password="test",
            auth_method="basic",
            message_encryption="invalid_value",
        )
    assert "invalid message_encryption arg: invalid_value. Should be 'auto', 'always', or 'never'" == str(exc.value)


@mock.patch("requests.Session")
def test_close_session(mock_session):
    t_default = transport.Transport(
        endpoint="Endpoint",
        server_cert_validation="ignore",
        username="test",
        password="test",
        auth_method="basic",
    )
    t_default.build_session()
    t_default.close_session()
    mock_session.return_value.close.assert_called_once_with()
    assert t_default.session is None


@mock.patch("requests.Session")
def test_close_session_not_built(mock_session):
    t_default = transport.Transport(
        endpoint="Endpoint",
        server_cert_validation="ignore",
        username="test",
        password="test",
        auth_method="basic",
    )
    t_default.close_session()
    assert mock_session.return_value.close.called is False
    assert t_default.session is None
