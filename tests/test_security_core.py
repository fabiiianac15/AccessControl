import base64
import os
import stat
import time

import pytest
from cryptography.exceptions import InvalidTag

from portero import crypto, door, ledger
from portero.crypto import Keyring, load_keyring
from portero.db import migrate
from portero.reports import csv_safe, to_csv

KEY = b"k" * 32


class TestKeyring:
    def test_round_trip(self):
        keys = Keyring(os.urandom(32))
        assert keys.decrypt(keys.encrypt(b"plantilla", "template:1"), "template:1") == b"plantilla"

    def test_blob_cannot_be_moved_to_another_person(self):
        keys = Keyring(os.urandom(32))
        blob = keys.encrypt(b"plantilla", "template:1")
        with pytest.raises(InvalidTag):
            keys.decrypt(blob, "template:2")

    def test_other_master_key_cannot_decrypt(self):
        blob = Keyring(os.urandom(32)).encrypt(b"plantilla", "template:1")
        with pytest.raises(InvalidTag):
            Keyring(os.urandom(32)).decrypt(blob, "template:1")

    def test_same_plaintext_encrypts_differently(self):
        keys = Keyring(os.urandom(32))
        assert keys.encrypt(b"x", "c") != keys.encrypt(b"x", "c")

    def test_rejects_short_key(self):
        with pytest.raises(ValueError):
            Keyring(b"corta")

    def test_generated_key_is_private_and_stable(self, tmp_path):
        first = load_keyring(None, tmp_path)
        blob = first.encrypt(b"dato", "c")
        assert stat.S_IMODE((tmp_path / "secret.key").stat().st_mode) == 0o600
        assert load_keyring(None, tmp_path).decrypt(blob, "c") == b"dato"

    def test_key_from_environment_is_not_written_to_disk(self, tmp_path):
        load_keyring(base64.b64encode(os.urandom(32)).decode(), tmp_path)
        assert not (tmp_path / "secret.key").exists()


class TestPasswords:
    def test_verify(self):
        stored = crypto.hash_password("una-contrasena-larga")
        assert crypto.verify_password(stored, "una-contrasena-larga")
        assert not crypto.verify_password(stored, "otra")

    def test_missing_user_never_verifies(self):
        assert not crypto.verify_password(None, "cualquiera")

    def test_corrupt_hash_fails_closed(self):
        assert not crypto.verify_password("no-es-un-hash", "cualquiera")


class TestLedger:
    def _events(self, conn, count=3):
        for index in range(count):
            ledger.record_event(
                conn,
                KEY,
                kiosk_id=1,
                zone_id=1,
                person_id=index,
                method="face",
                outcome="granted",
                reason="ok",
                score=0.7,
            )

    def test_intact_chain_verifies(self, conn):
        self._events(conn)
        report = ledger.verify_events(conn, KEY)
        assert report.ok and report.rows == 3

    def test_edited_outcome_is_detected(self, conn):
        self._events(conn)
        conn.execute("UPDATE events SET outcome = 'denied' WHERE id = 2")
        report = ledger.verify_events(conn, KEY)
        assert not report.ok and report.broken_id == 2

    def test_deleted_middle_row_is_detected(self, conn):
        self._events(conn)
        conn.execute("DELETE FROM events WHERE id = 2")
        report = ledger.verify_events(conn, KEY)
        assert not report.ok and report.broken_id == 3

    def test_attacker_without_key_cannot_forge_a_row(self, conn):
        self._events(conn)
        last = conn.execute("SELECT hash FROM events ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.execute(
            """INSERT INTO events (ts, method, outcome, reason, prev_hash, hash)
               VALUES ('2026-01-01', 'face', 'granted', 'ok', ?, ?)""",
            (last, "f" * 64),
        )
        assert not ledger.verify_events(conn, KEY).ok

    def test_wrong_key_fails_verification(self, conn):
        self._events(conn)
        assert not ledger.verify_events(conn, b"z" * 32).ok

    def test_retention_of_oldest_rows_keeps_chain_valid(self, conn):
        self._events(conn, 5)
        conn.execute("DELETE FROM events WHERE id <= 2")
        assert ledger.verify_events(conn, KEY).ok

    def test_door_status_is_not_part_of_the_signature(self, conn):
        self._events(conn, 1)
        conn.execute("UPDATE events SET door_status = 'failed'")
        assert ledger.verify_events(conn, KEY).ok

    def test_audit_chain_detects_edits(self, conn):
        ledger.record_audit(conn, KEY, "coordinador", "person.create", "persona:1")
        ledger.record_audit(conn, KEY, "coordinador", "person.erase", "persona:1")
        assert ledger.verify_audit(conn, KEY).ok
        conn.execute("UPDATE audit_log SET actor = 'otro' WHERE id = 1")
        assert not ledger.verify_audit(conn, KEY).ok


def test_migrations_are_idempotent(conn):
    migrate(conn)
    assert conn.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 0


class TestDoorSignature:
    def test_valid(self):
        stamp = str(int(time.time()))
        signature = door.sign("s", stamp, b"{}")
        assert door.verify_signature("s", stamp, b"{}", signature)

    def test_altered_body(self):
        stamp = str(int(time.time()))
        assert not door.verify_signature("s", stamp, b'{"x":1}', door.sign("s", stamp, b"{}"))

    def test_replay_outside_window_is_rejected(self):
        stamp = "1000"
        signature = door.sign("s", stamp, b"{}")
        assert door.verify_signature("s", stamp, b"{}", signature, now=1010)
        assert not door.verify_signature("s", stamp, b"{}", signature, now=1000 + 31)

    def test_garbage_timestamp(self):
        assert not door.verify_signature("s", "ayer", b"{}", "x")

    def test_unreachable_door_reports_failure_without_raising(self):
        assert door.DoorClient(timeout=0.2).open("http://127.0.0.1:9/x", "s", {}) == "failed"


class TestCsv:
    @pytest.mark.parametrize("text", ["=1+1", "+57", "-2", "@SUM(A1)", "\tx", "\rx"])
    def test_formula_like_cells_are_neutralized(self, text):
        assert csv_safe(text).startswith("'")

    def test_regular_values_are_untouched(self):
        assert csv_safe("Laura Sanjuán") == "Laura Sanjuán"
        assert csv_safe(None) == ""

    def test_excel_friendly_format(self):
        content = to_csv(["A", "B"], [["=x", "ñ"]])
        assert content.startswith("﻿A;B")
        assert "'=x;ñ" in content
