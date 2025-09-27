from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app.execution.errors import ExecutionError
from app.execution.permit2 import Permit2Allowance, Permit2Authorizer


class _StubAccount:
    def sign_message(self, _encoded, private_key: str):  # pragma: no cover - simple stub
        assert private_key == "0xabc"
        return SimpleNamespace(signature=b"\xaa" * 64)


class _StubEth:
    def __init__(self, chain_id: int = 11155111):
        self.chain_id = chain_id
        self.account = _StubAccount()


class _StubWeb3:
    def __init__(self, chain_id: int = 11155111):
        self.eth = _StubEth(chain_id=chain_id)


class _StubSigner:
    def __init__(self, chain_id: int = 11155111):
        self.address = "0x00000000000000000000000000000000000000AA"
        self.private_key = "0xabc"
        self.w3 = _StubWeb3(chain_id=chain_id)


@pytest.fixture()
def stub_authorizer() -> Permit2Authorizer:
    signer = _StubSigner()
    return Permit2Authorizer(
        signer,
        enabled=True,
        contract_address="0x00000000000000000000000000000000000000BB",
        default_spender="0x00000000000000000000000000000000000000CC",
        default_expiration_seconds=600,
        min_validity_seconds=60,
    )


def test_build_permit_creates_signature_when_insufficient_allowance(monkeypatch, stub_authorizer):
    now = int(time.time())
    monkeypatch.setattr(
        stub_authorizer,
        "allowance",
        lambda token, spender=None: Permit2Allowance(amount=0, expiration=now - 10, nonce=7),
    )

    payload = stub_authorizer.build_permit(
        token="0x00000000000000000000000000000000000000DD",
        spender="0x00000000000000000000000000000000000000EE",
        required_amount=1234,
    )
    assert payload is not None
    assert payload.permit["details"]["amount"] == 1234
    assert payload.permit["details"]["nonce"] == 7
    assert payload.signature.startswith("0x")


def test_build_permit_returns_none_when_allowance_sufficient(monkeypatch, stub_authorizer):
    now = int(time.time())
    monkeypatch.setattr(
        stub_authorizer,
        "allowance",
        lambda token, spender=None: Permit2Allowance(amount=5000, expiration=now + 5_000, nonce=3),
    )

    payload = stub_authorizer.build_permit(
        token="0x00000000000000000000000000000000000000DD",
        spender="0x00000000000000000000000000000000000000EE",
        required_amount=1000,
    )
    assert payload is None


def test_build_permit_disabled_returns_none():
    signer = _StubSigner()
    authorizer = Permit2Authorizer(
        signer,
        enabled=False,
        contract_address=None,
        default_spender=None,
    )
    payload = authorizer.build_permit(
        token="0x00000000000000000000000000000000000000DD",
        spender=None,
        required_amount=50,
    )
    assert payload is None


def test_build_permit_raises_on_oversized_amount(stub_authorizer):
    with pytest.raises(Exception):
        stub_authorizer.build_permit(
            token="0x00000000000000000000000000000000000000DD",
            spender=None,
            required_amount=(1 << 161),
        )


def test_needs_permit_checks_expiration(monkeypatch, stub_authorizer):
    now = int(time.time())
    monkeypatch.setattr(
        stub_authorizer,
        "allowance",
        lambda token, spender=None: Permit2Allowance(amount=999, expiration=now + 10, nonce=1),
    )
    assert stub_authorizer.needs_permit(
        token="0x00000000000000000000000000000000000000DD",
        spender=None,
        required_amount=1000,
    )

    monkeypatch.setattr(
        stub_authorizer,
        "allowance",
        lambda token, spender=None: Permit2Allowance(amount=2000, expiration=now + 5_000, nonce=2),
    )
    assert not stub_authorizer.needs_permit(
        token="0x00000000000000000000000000000000000000DD",
        spender=None,
        required_amount=1000,
    )


def test_build_permit_requires_spender():
    signer = _StubSigner()
    authorizer = Permit2Authorizer(
        signer,
        enabled=True,
        contract_address="0x00000000000000000000000000000000000000BB",
        default_spender=None,
    )
    with pytest.raises(ExecutionError):
        authorizer.build_permit(
            token="0x00000000000000000000000000000000000000DD",
            spender=None,
            required_amount=10,
        )