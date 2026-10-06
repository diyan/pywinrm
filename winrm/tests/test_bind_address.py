from __future__ import annotations

import pytest
import requests

import winrm.transport as transport_module
from winrm.exceptions import WinRMError
from winrm.protocol import Protocol
from winrm.transport import Transport


class DummySourceAddressAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, source_address: str) -> None:
        super().__init__()
        self.source_address = source_address


def create_transport(bind_address: str | None = None) -> Transport:
    return Transport(
        endpoint="https://server.example.test:5986/wsman",
        username="user",
        password="password",
        auth_method="basic",
        server_cert_validation="ignore",
        proxy=None,
        bind_address=bind_address,
    )


def test_build_session_mounts_source_address_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(transport_module, "HAVE_REQUESTS_TOOLBELT", True)
    monkeypatch.setattr(
        transport_module,
        "SourceAddressAdapter",
        DummySourceAddressAdapter,
        raising=False,
    )

    session = create_transport(bind_address="192.0.2.10").build_session()

    http_adapter = session.adapters["http://"]
    https_adapter = session.adapters["https://"]

    assert isinstance(http_adapter, DummySourceAddressAdapter)
    assert isinstance(https_adapter, DummySourceAddressAdapter)
    assert http_adapter.source_address == "192.0.2.10"
    assert https_adapter.source_address == "192.0.2.10"


def test_build_session_requires_requests_toolbelt_for_bind_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport_module, "HAVE_REQUESTS_TOOLBELT", False)

    with pytest.raises(WinRMError, match="bind_address requires requests-toolbelt"):
        create_transport(bind_address="192.0.2.10").build_session()


def test_build_session_does_not_require_requests_toolbelt_without_bind_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport_module, "HAVE_REQUESTS_TOOLBELT", False)

    session = create_transport().build_session()

    assert isinstance(session.adapters["http://"], requests.adapters.HTTPAdapter)
    assert isinstance(session.adapters["https://"], requests.adapters.HTTPAdapter)


def test_protocol_passes_bind_address_to_transport() -> None:
    protocol = Protocol(
        endpoint="https://server.example.test:5986/wsman",
        transport="basic",
        username="user",
        password="password",
        server_cert_validation="ignore",
        proxy=None,
        bind_address="192.0.2.10",
    )

    assert protocol.transport.bind_address == "192.0.2.10"
