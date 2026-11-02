import pytest

from portero import cli
from portero.config import Settings
from portero.db import connect


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PORTERO_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("PORTERO_MASTER_KEY", raising=False)
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": None})
    return tmp_path


def test_admin_rejects_short_password(data_dir, capsys):
    assert cli.main(["admin", "coordinador", "--password", "corta"]) == 1
    assert "12 caracteres" in capsys.readouterr().err


def test_admin_create_and_reset_closes_sessions(data_dir):
    assert cli.main(["admin", "coordinador", "--password", "una-contrasena-larga"]) == 0
    conn = connect(data_dir / "portero.db")
    admin = conn.execute("SELECT * FROM admins").fetchone()
    assert admin["role"] == "admin" and "una-contrasena" not in admin["password_hash"]
    conn.execute(
        """INSERT INTO sessions (token_hash, admin_id, csrf_token, expires_at)
           VALUES ('x', ?, 'c', '2999')""",
        (admin["id"],),
    )
    assert (
        cli.main(
            ["admin", "coordinador", "--password", "otra-contrasena-larga", "--role", "viewer"]
        )
        == 0
    )
    assert conn.execute("SELECT role FROM admins").fetchone()[0] == "viewer"
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_demo_only_on_empty_database_and_has_no_biometrics(data_dir, capsys):
    assert cli.main(["demo"]) == 0
    conn = connect(data_dir / "portero.db")
    assert conn.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 12
    assert conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] > 100
    assert cli.main(["demo"]) == 1


def test_audit_reports_tampering_with_exit_code(data_dir, capsys):
    assert cli.main(["demo"]) == 0
    assert cli.main(["audit"]) == 0
    assert "íntegra" in capsys.readouterr().out
    conn = connect(data_dir / "portero.db")
    conn.execute("UPDATE events SET outcome = 'granted' WHERE outcome = 'denied'")
    assert cli.main(["audit"]) == 1
    assert "ROTA" in capsys.readouterr().out


def test_purge(data_dir, capsys):
    assert cli.main(["demo"]) == 0
    assert cli.main(["purge"]) == 0
    assert "Eventos borrados: 0" in capsys.readouterr().out
    conn = connect(data_dir / "portero.db")
    conn.execute("UPDATE events SET ts = '2001-01-01T00:00:00.000+00:00' WHERE id = 1")
    assert cli.main(["purge"]) == 0
    assert "Eventos borrados: 1" in capsys.readouterr().out
    assert conn.execute("SELECT 1 FROM audit_log WHERE action = 'retention.purge'").fetchone()
