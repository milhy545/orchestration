"""Unit tests for the gateway wrappers; no gateway process is required."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]


def load(path: str, name: str):
    source = ROOT / path
    loader = importlib.machinery.SourceFileLoader(name, str(source))
    spec = importlib.util.spec_from_file_location(name, source, loader=loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = load("scripts/mega_security", "mega_security_cli_test")
funnel = load("scripts/mega_funnel", "mega_funnel_cli_test")


class FakeSocket:
    def __init__(self, response: dict):
        self.response = (json.dumps(response) + "\n").encode()
        self.sent = b""
        self.connected = None

    def settimeout(self, value):
        self.timeout = value

    def connect(self, path):
        self.connected = path

    def sendall(self, data):
        self.sent += data

    def recv(self, _size):
        response, self.response = self.response, b""
        return response

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def factory_for(fake):
    return lambda *_args: fake


def test_client_sends_action_and_payload():
    fake = FakeSocket({"ok": True, "data": {"state": "ready"}})
    client = cli.AdminClient("/tmp/test.sock", socket_factory=factory_for(fake))

    assert client.request("pairing.approve", pairing_id="pair-7") == {"state": "ready"}
    assert fake.connected == "/tmp/test.sock"
    assert json.loads(fake.sent) == {
        "action": "pairing.approve", "payload": {"pairing_id": "pair-7"}
    }


@pytest.mark.parametrize(
    ("command", "expected"),
    [("status", "status"), ("audit", "audit.recent"),
     ("backup-check", "backup.config.check")],
)
def test_read_and_emergency_actions(command, expected):
    fake = FakeSocket({"ok": True, "data": []})
    client = cli.AdminClient(socket_factory=factory_for(fake))
    args = cli._parser().parse_args([command])
    cli.run(client, args)
    assert json.loads(fake.sent)["action"] == expected


def test_funnel_defaults_to_read_only_status():
    calls = []

    def execute(command, **_kwargs):
        calls.append(command)
        return type("Result", (), {"returncode": 0, "stdout": '{"enabled": false}', "stderr": ""})()

    assert funnel.run_funnel("status", runner=("fake",), execute=execute) == '{"enabled": false}'
    assert calls == [["fake", "status", "--json"]]


def test_funnel_off_only_disables():
    calls = []

    def execute(command, **_kwargs):
        calls.append(command)
        return type("Result", (), {"returncode": 0, "stdout": "disabled", "stderr": ""})()

    funnel.run_funnel("off", runner=("fake",), execute=execute)
    assert calls == [["fake", "off"]]


def test_funnel_rejects_enable_action(capsys):
    with pytest.raises(SystemExit) as exc:
        funnel.main(["on"])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_rejected_response_becomes_operator_error():
    fake = FakeSocket({"ok": False, "error": "policy denied"})
    with pytest.raises(cli.GatewayError, match="policy denied"):
        cli.AdminClient(socket_factory=factory_for(fake)).request("pairing.approve", pairing_id="pair-7")
