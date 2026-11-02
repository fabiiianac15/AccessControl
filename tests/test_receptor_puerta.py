"""El receptor de ejemplo debe interoperar con la firma real que envía Portero."""

import http.client
import importlib.util
import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from portero.door import DoorClient, sign

spec = importlib.util.spec_from_file_location(
    "receptor_puerta", Path(__file__).parents[1] / "examples" / "receptor_puerta.py"
)
receptor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receptor)


@pytest.fixture
def servidor(monkeypatch):
    abiertos = []
    monkeypatch.setattr(receptor, "abrir_cerradura", lambda: abiertos.append(1))
    receptor.Receptor.secreto = "secreto-puerta"
    receptor.Receptor.ya_vistos = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), receptor.Receptor)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    yield server.server_address[1], abiertos
    server.shutdown()


def enviar(port, body, stamp, signature, path="/abrir"):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    conn.request(
        "POST",
        path,
        body,
        {"X-Portero-Timestamp": stamp, "X-Portero-Signature": signature},
    )
    return conn.getresponse().status


def test_real_client_opens_the_door(servidor):
    port, abiertos = servidor
    url = f"http://127.0.0.1:{port}/abrir"
    assert DoorClient().open(url, "secreto-puerta", {"event": 1}) == "opened"
    assert abiertos == [1]


def test_wrong_secret_does_not_open(servidor):
    port, abiertos = servidor
    url = f"http://127.0.0.1:{port}/abrir"
    assert DoorClient().open(url, "otro", {"event": 1}) == "failed"
    assert abiertos == []


def test_replay_of_captured_request_does_not_open_twice(servidor):
    port, abiertos = servidor
    body = json.dumps({"event": 7}).encode()
    stamp = str(int(time.time()))
    signature = sign("secreto-puerta", stamp, body)
    assert enviar(port, body, stamp, signature) == 200
    assert enviar(port, body, stamp, signature) == 409
    assert abiertos == [1]


def test_old_signature_is_rejected(servidor):
    port, abiertos = servidor
    body = json.dumps({"event": 8}).encode()
    stamp = str(int(time.time()) - 120)
    assert enviar(port, body, stamp, sign("secreto-puerta", stamp, body)) == 401
    assert abiertos == []
