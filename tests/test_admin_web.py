"""Panel de administración: sesión, permisos, consentimiento y derechos del titular."""

import json
from datetime import timedelta

import pytest

from conftest import FIXED_NOW, PASSWORD, create_admin, enroll, face, login, seed_person, unit
from portero import ledger, people
from portero.web.deps import SESSION_COOKIE


def post(client, url, csrf, **data):
    return client.post(url, data={"csrf": csrf, **data})


class TestAuth:
    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/personas",
            "/puertas",
            "/eventos",
            "/eventos.csv",
            "/asistencia",
            "/bitacora",
            "/privacidad",
            "/cuenta",
            "/personas/1",
            "/personas/1/exportar",
        ],
    )
    def test_pages_require_session(self, client, path):
        response = client.get(path)
        assert response.status_code == 303 and response.headers["location"] == "/login"

    def test_api_answers_401_instead_of_redirecting(self, client):
        assert client.get("/api/eventos/recientes").status_code == 401

    def test_cookie_flags(self, client, state):
        with state.db() as conn:
            create_admin(conn)
        response = client.post("/login", data={"username": "coordinador", "password": PASSWORD})
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=lax" in cookie

    def test_secure_flag_on_https(self, app, state):
        from fastapi.testclient import TestClient

        with state.db() as conn:
            create_admin(conn)
        https = TestClient(app, base_url="https://portero.local", follow_redirects=False)
        response = https.post("/login", data={"username": "coordinador", "password": PASSWORD})
        assert "secure" in response.headers["set-cookie"].lower()

    def test_session_token_is_not_stored_in_plain(self, client, state):
        with state.db() as conn:
            create_admin(conn)
        login(client)
        token = client.cookies[SESSION_COOKIE]
        with state.db() as conn:
            stored = conn.execute("SELECT token_hash FROM sessions").fetchone()[0]
        assert token != stored

    def test_wrong_password_and_unknown_user_look_alike(self, client, state):
        with state.db() as conn:
            create_admin(conn)
        wrong = client.post("/login", data={"username": "coordinador", "password": "x"})
        unknown = client.post("/login", data={"username": "nadie", "password": "x"})
        assert wrong.status_code == unknown.status_code == 401
        assert "incorrectos" in wrong.text and "incorrectos" in unknown.text

    def test_lockout_after_repeated_failures(self, client, state):
        with state.db() as conn:
            create_admin(conn)
        for _ in range(5):
            client.post("/login", data={"username": "coordinador", "password": "x"})
        blocked = client.post("/login", data={"username": "coordinador", "password": PASSWORD})
        assert blocked.status_code == 429

    def test_expired_session_is_rejected(self, admin_client, state):
        client, _ = admin_client
        with state.db() as conn:
            conn.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00.000+00:00'")
        assert client.get("/").status_code == 303

    def test_logout_invalidates_session_on_server(self, admin_client, state):
        client, csrf = admin_client
        token = client.cookies[SESSION_COOKIE]
        assert post(client, "/logout", csrf).status_code == 303
        client.cookies.set(SESSION_COOKIE, token)
        assert client.get("/").status_code == 303

    def test_change_password_closes_sessions(self, admin_client):
        client, csrf = admin_client
        response = post(
            client, "/cuenta/contrasena", csrf, current=PASSWORD, new="otra-contrasena-larga"
        )
        assert response.headers["location"] == "/login"
        assert client.get("/").status_code == 303
        assert (
            client.post(
                "/login", data={"username": "coordinador", "password": "otra-contrasena-larga"}
            ).status_code
            == 303
        )

    def test_change_password_rejects_short_or_wrong_current(self, admin_client):
        client, csrf = admin_client
        short = post(client, "/cuenta/contrasena", csrf, current=PASSWORD, new="corta")
        wrong = post(
            client, "/cuenta/contrasena", csrf, current="mala", new="otra-contrasena-larga"
        )
        assert "password_bad" in short.headers["location"]
        assert "password_bad" in wrong.headers["location"]


class TestCsrfAndRoles:
    def test_post_without_token_is_forbidden(self, admin_client):
        client, _ = admin_client
        assert client.post("/personas/nueva", data={"full_name": "Sergio Lobo"}).status_code == 403

    def test_post_with_wrong_token_is_forbidden(self, admin_client):
        client, _ = admin_client
        assert post(client, "/personas/nueva", "falso", full_name="Sergio Lobo").status_code == 403

    def test_api_needs_header_token(self, admin_client, state, frame_bytes):
        client, _ = admin_client
        with state.db() as conn:
            person = seed_person(conn)
        assert (
            client.post(f"/api/personas/{person}/muestras", content=frame_bytes).status_code == 403
        )

    @pytest.fixture
    def viewer(self, client, state):
        with state.db() as conn:
            create_admin(conn, "auditora", "viewer")
            person = seed_person(conn)
        return client, login(client, "auditora"), person

    def test_viewer_can_read(self, viewer):
        client, _, person = viewer
        assert client.get("/").status_code == 200
        assert client.get(f"/personas/{person}").status_code == 200

    def test_viewer_sees_no_write_controls(self, viewer):
        client, _, person = viewer
        page = client.get(f"/personas/{person}").text
        assert "Suprimir persona" not in page and "Generar PIN" not in page

    @pytest.mark.parametrize("action", ["suprimir", "pin", "autorizacion/retirar", "rostro/borrar"])
    def test_viewer_cannot_write(self, viewer, action):
        client, csrf, person = viewer
        assert post(client, f"/personas/{person}/{action}", csrf).status_code == 403

    def test_viewer_cannot_export_biometric_data(self, viewer):
        client, _, person = viewer
        assert client.get(f"/personas/{person}/exportar").status_code == 403

    def test_viewer_may_change_own_password(self, viewer):
        client, csrf, _ = viewer
        response = post(
            client, "/cuenta/contrasena", csrf, current=PASSWORD, new="otra-contrasena-larga"
        )
        assert response.headers["location"] == "/login"


class TestSecurityHeaders:
    def test_headers_on_public_page(self, client):
        response = client.get("/login")
        csp = response.headers["content-security-policy"]
        assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
        assert "unsafe-inline" not in csp
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "no-store"

    def test_no_api_docs_exposed(self, client):
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404

    def test_names_are_escaped(self, admin_client):
        client, csrf = admin_client
        response = post(client, "/personas/nueva", csrf, full_name="<script>alert(1)</script>")
        page = client.get(response.headers["location"]).text
        assert "<script>alert(1)</script>" not in page
        assert "&lt;script&gt;" in page

    def test_templates_have_no_inline_scripts_or_styles(self):
        """La CSP los bloquearía: si alguien agrega uno, debe fallar aquí y no en producción."""
        from pathlib import Path

        import portero.web

        for path in (Path(portero.web.__file__).parent / "templates").glob("*.html"):
            text = path.read_text()
            assert " style=" not in text, path.name
            assert " onclick=" not in text, path.name
            for chunk in text.split("<script")[1:]:
                assert chunk.lstrip().startswith("src="), path.name


class TestPeople:
    def test_create_and_edit(self, admin_client, state):
        client, csrf = admin_client
        created = post(
            client,
            "/personas/nueva",
            csrf,
            full_name=" Natalia Ascanio ",
            document="1091",
            group_name="Monitores",
        )
        location = created.headers["location"].split("?")[0]
        person = int(location.rsplit("/", 1)[1])
        assert "Natalia Ascanio" in client.get("/personas").text
        post(client, f"{location}/editar", csrf, full_name="Natalia Ascanio Páez", group_name="X")
        with state.db() as conn:
            row = conn.execute("SELECT * FROM people WHERE id = ?", (person,)).fetchone()
            actions = [r[0] for r in conn.execute("SELECT action FROM audit_log")]
        assert row["full_name"] == "Natalia Ascanio Páez"
        assert row["active"] == 0  # casilla sin marcar
        assert "person.create" in actions and "person.update" in actions

    def test_search_treats_wildcards_literally(self, admin_client, state):
        client, _ = admin_client
        with state.db() as conn:
            seed_person(conn, "Andrés Ropero")
        assert "Andrés Ropero" in client.get("/personas", params={"q": "Ropero"}).text
        assert "Andrés Ropero" not in client.get("/personas", params={"q": "%"}).text

    def test_missing_person_is_404_page(self, admin_client):
        client, _ = admin_client
        response = client.get("/personas/9999")
        assert response.status_code == 404 and "Portero" in response.text


class TestGrants:
    @pytest.fixture
    def ctx(self, admin_client, state):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
            zone = conn.execute("INSERT INTO zones (name) VALUES ('Lab')").lastrowid
        return client, csrf, person, zone

    def add(self, client, csrf, person, zone, **extra):
        data = {
            "csrf": csrf,
            "zone_id": zone,
            "days": ["0", "4"],
            "start": "08:00",
            "end": "17:00",
            **extra,
        }
        return client.post(f"/personas/{person}/permisos", data=data)

    def test_mask_and_minutes(self, ctx, state):
        client, csrf, person, zone = ctx
        assert "grant_saved" in self.add(client, csrf, person, zone).headers["location"]
        with state.db() as conn:
            grant = conn.execute("SELECT * FROM grants").fetchone()
        assert grant["weekdays"] == 0b10001
        assert (grant["start_minute"], grant["end_minute"]) == (480, 1020)

    def test_overnight_allowed(self, ctx, state):
        client, csrf, person, zone = ctx
        self.add(client, csrf, person, zone, start="22:00", end="06:00")
        with state.db() as conn:
            assert conn.execute("SELECT start_minute FROM grants").fetchone()[0] == 1320

    def test_end_at_midnight_means_end_of_day(self, ctx, state):
        client, csrf, person, zone = ctx
        self.add(client, csrf, person, zone, start="08:00", end="00:00")
        with state.db() as conn:
            assert conn.execute("SELECT end_minute FROM grants").fetchone()[0] == 1440

    @pytest.mark.parametrize(
        "extra",
        [
            {"days": []},
            {"start": "25:00"},
            {"start": "08:00", "end": "08:00"},
            {"valid_from": "2026-03-10", "valid_until": "2026-03-01"},
            {"valid_until": "mañana"},
            {"zone_id": 9999},
        ],
    )
    def test_invalid_grant_rejected(self, ctx, state, extra):
        client, csrf, person, zone = ctx
        response = self.add(client, csrf, person, zone, **extra)
        assert "grant_bad" in response.headers["location"]
        with state.db() as conn:
            assert conn.execute("SELECT COUNT(*) FROM grants").fetchone()[0] == 0


class TestConsentAndEnrollment:
    def sample(self, client, csrf, person, frame):
        return client.post(
            f"/api/personas/{person}/muestras", content=frame, headers={"X-CSRF-Token": csrf}
        )

    def test_biometric_enrollment_blocked_without_consent(
        self, admin_client, state, engine, frame_bytes
    ):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn, consent=False)
        engine.queue([face()], unit(1))
        result = self.sample(client, csrf, person, frame_bytes).json()
        assert result["accepted"] is False and result["code"] == "no_consent"
        with state.db() as conn:
            assert people.template_count(conn, person) == 0

    def test_consent_needs_explicit_confirmation(self, admin_client, state):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn, consent=False)
        missing = post(client, f"/personas/{person}/autorizacion", csrf, evidence="folio 12")
        assert missing.status_code == 422
        ok = post(
            client, f"/personas/{person}/autorizacion", csrf, evidence="folio 12", confirmed="1"
        )
        assert "consent_saved" in ok.headers["location"]
        with state.db() as conn:
            row = people.active_consent(conn, person)
        assert row["evidence"] == "folio 12" and row["recorded_by"] == "coordinador"
        assert row["policy_version"] == people.POLICY_VERSION

    def test_enroll_flow_stores_encrypted_and_recognizes(
        self, admin_client, state, engine, frame_bytes
    ):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
        engine.queue([face()], unit(1))
        result = self.sample(client, csrf, person, frame_bytes).json()
        assert result["accepted"] is True and result["samples"] == 1
        assert state.gallery.match(unit(1)).person_id == person

    def test_rejects_face_of_another_registered_person(
        self, admin_client, state, engine, frame_bytes
    ):
        client, csrf = admin_client
        with state.db() as conn:
            first = seed_person(conn, "Laura Sanjuán")
            second = seed_person(conn, "Diego Pacheco")
            enroll(state, conn, first, unit(1))
        engine.queue([face()], unit(1))
        result = self.sample(client, csrf, second, frame_bytes).json()
        assert result["code"] == "duplicate" and result["accepted"] is False

    def test_rejects_sample_of_someone_else_for_same_person(
        self, admin_client, state, engine, frame_bytes
    ):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
            enroll(state, conn, person, unit(1))
        engine.queue([face()], unit(2))
        assert self.sample(client, csrf, person, frame_bytes).json()["code"] == "other_person"

    @pytest.mark.parametrize(
        "faces,code",
        [([], "no_face"), ([face(), face()], "many_faces"), ([face(yaw=0.35)], "not_frontal")],
    )
    def test_rejects_bad_frames(self, admin_client, state, engine, frame_bytes, faces, code):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
        engine.queue(faces, unit(1))
        assert self.sample(client, csrf, person, frame_bytes).json()["code"] == code

    def test_sample_limit(self, admin_client, state, settings, frame_bytes):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
            for _ in range(settings.max_samples):
                enroll(state, conn, person, unit(1))
        assert self.sample(client, csrf, person, frame_bytes).json()["code"] == "full"

    def test_revoking_consent_deletes_templates_but_keeps_pin(self, admin_client, state):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
            enroll(state, conn, person, unit(1))
            people.assign_pin(state, conn, person)
        assert state.gallery.match(unit(1)).person_id == person
        response = post(client, f"/personas/{person}/autorizacion/retirar", csrf)
        assert "consent_revoked" in response.headers["location"]
        assert state.gallery.match(unit(1)).person_id is None
        with state.db() as conn:
            assert people.template_count(conn, person) == 0
            row = conn.execute("SELECT pin_lookup FROM people WHERE id = ?", (person,)).fetchone()
            consent = conn.execute("SELECT revoked_by FROM consents").fetchone()
        assert row["pin_lookup"] is not None
        assert consent["revoked_by"] == "coordinador"

    def test_deactivating_person_removes_from_recognition(self, admin_client, state):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
            enroll(state, conn, person, unit(1))
        post(client, f"/personas/{person}/editar", csrf, full_name="Camilo Quintero")
        assert state.gallery.match(unit(1)).person_id is None

    def test_consent_form_states_alternative_and_rights(self, admin_client, state):
        client, _ = admin_client
        with state.db() as conn:
            person = seed_person(conn, "Laura Sanjuán", consent=False)
        page = client.get(f"/personas/{person}/autorizacion/imprimir").text
        for expected in (
            "Laura Sanjuán",
            "UFPSO Pruebas",
            "Ley 1581",
            "PIN",
            "es voluntario",
            "Superintendencia de Industria y Comercio",
            people.POLICY_VERSION,
        ):
            assert expected in page


class TestPin:
    def test_pin_shown_once_and_stored_only_as_hmac(self, admin_client, state):
        client, csrf = admin_client
        with state.db() as conn:
            person = seed_person(conn)
        page = post(client, f"/personas/{person}/pin", csrf)
        assert page.status_code == 200
        import re

        pin = re.search(r'class="pin-big"[^>]*>(\d{6})<', page.text).group(1)
        assert pin not in client.get(f"/personas/{person}").text
        with state.db() as conn:
            stored = conn.execute("SELECT pin_lookup FROM people").fetchone()[0]
        assert stored == state.keys.pin_lookup(pin) and pin not in stored

    def test_pin_collision_retries(self, state, monkeypatch):
        with state.db() as conn:
            first, second = seed_person(conn, "A B"), seed_person(conn, "C D")
            values = iter(["111111", "111111", "222222"])
            monkeypatch.setattr("portero.crypto.new_pin", lambda: next(values))
            assert people.assign_pin(state, conn, first) == "111111"
            assert people.assign_pin(state, conn, second) == "222222"


class TestErasure:
    def test_erase_removes_personal_data_and_keeps_chain(self, admin_client, state, settings):
        client, csrf = admin_client
        settings.photos_dir.mkdir(parents=True)
        photo = settings.photos_dir / "2026-01-01-aa.enc"
        photo.write_bytes(b"x")
        with state.db() as conn:
            person = seed_person(conn, "Laura Sanjuán")
            enroll(state, conn, person, unit(1))
            people.assign_pin(state, conn, person)
            ledger.record_event(
                conn,
                state.keys.chain_key,
                kiosk_id=None,
                zone_id=None,
                person_id=person,
                method="face",
                outcome="granted",
                reason="ok",
                photo_file=photo.name,
            )
        wrong = post(client, f"/personas/{person}/suprimir", csrf, confirm="otro nombre")
        assert wrong.status_code == 422

        done = post(client, f"/personas/{person}/suprimir", csrf, confirm="Laura Sanjuán")
        assert "person_erased" in done.headers["location"]
        assert not photo.exists()
        with state.db() as conn:
            for table in ("people", "templates", "consents"):
                assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
            event = conn.execute("SELECT * FROM events").fetchone()
            assert event["person_id"] == person and event["photo_file"] is None
            assert ledger.verify_events(conn, state.keys.chain_key).ok
            assert ledger.verify_audit(conn, state.keys.chain_key).ok
        assert state.gallery.match(unit(1)).person_id is None
        events_page = client.get("/eventos").text
        assert f"Persona suprimida #{person}" in events_page
        assert "Laura Sanjuán" not in events_page

    def test_export_contains_everything_held(self, admin_client, state):
        client, _ = admin_client
        with state.db() as conn:
            person = seed_person(conn, "Laura Sanjuán")
            enroll(state, conn, person, unit(1))
            ledger.record_event(
                conn,
                state.keys.chain_key,
                kiosk_id=None,
                zone_id=None,
                person_id=person,
                method="face",
                outcome="granted",
                reason="ok",
            )
        response = client.get(f"/personas/{person}/exportar")
        data = json.loads(response.text)
        assert "attachment" in response.headers["content-disposition"]
        assert data["persona"]["nombre"] == "Laura Sanjuán"
        assert len(data["plantillas_faciales"]) == 1
        assert data["plantillas_faciales"][0]["vector_base64"]
        assert len(data["autorizaciones"]) == 1 and len(data["eventos"]) == 1
        with state.db() as conn:
            assert conn.execute("SELECT 1 FROM audit_log WHERE action = 'person.export'").fetchone()


class TestRetention:
    def test_purge_old_events_keeps_recent_and_chain(self, admin_client, state, settings):
        client, csrf = admin_client
        state.clock = lambda: FIXED_NOW
        settings.photos_dir.mkdir(parents=True)
        old_photo = settings.photos_dir / "old.enc"
        old_photo.write_bytes(b"x")
        with state.db() as conn:
            key = state.keys.chain_key
            common = {
                "kiosk_id": None,
                "zone_id": None,
                "person_id": None,
                "method": "face",
                "outcome": "denied",
                "reason": "unknown_face",
            }
            ledger.record_event(
                conn,
                key,
                **common,
                photo_file="old.enc",
                when=FIXED_NOW - timedelta(days=settings.retention_days + 1),
            )
            ledger.record_event(conn, key, **common, when=FIXED_NOW - timedelta(days=1))
        page = post(client, "/privacidad/purgar", csrf)
        assert page.status_code == 200 and "Se borraron 1 eventos" in page.text
        assert not old_photo.exists()
        with state.db() as conn:
            assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
            assert ledger.verify_events(conn, state.keys.chain_key).ok
            anchor = conn.execute(
                "SELECT details FROM audit_log WHERE action = 'retention.purge'"
            ).fetchone()
        assert "último hash" in anchor[0]


class TestDoorsAndKiosks:
    def _zone(self, client, csrf, name="Lab"):
        assert post(client, "/puertas/zonas", csrf, name=name).status_code == 303

    def test_kiosk_link_shown_once_and_token_hashed(self, admin_client, state):
        client, csrf = admin_client
        self._zone(client, csrf)
        page = post(client, "/puertas/kioscos", csrf, name="Entrada", zone_id=1)
        assert page.status_code == 200
        import re

        token = re.search(r"kiosco#token=([\w-]+)", page.text).group(1)
        with state.db() as conn:
            assert token not in conn.execute("SELECT token_hash FROM kiosks").fetchone()[0]
        assert token not in client.get("/puertas").text
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/kiosk/v1/config", headers=headers).json()["name"] == "Entrada"

    def test_door_secret_encrypted(self, admin_client, state):
        client, csrf = admin_client
        self._zone(client, csrf)
        page = post(
            client,
            "/puertas/kioscos",
            csrf,
            name="Entrada",
            zone_id=1,
            door_webhook_url="http://192.168.1.50:9000/abrir",
        )
        assert "Secreto para verificar" in page.text
        with state.db() as conn:
            assert conn.execute("SELECT door_secret FROM kiosks").fetchone()[0] is not None

    @pytest.mark.parametrize(
        "url", ["ftp://x/y", "file:///etc/passwd", "javascript:alert(1)", "nada"]
    )
    def test_invalid_webhook_rejected(self, admin_client, url):
        client, csrf = admin_client
        self._zone(client, csrf)
        response = post(
            client, "/puertas/kioscos", csrf, name="Entrada", zone_id=1, door_webhook_url=url
        )
        assert response.status_code == 422

    def test_zone_with_kiosk_cannot_be_deleted(self, admin_client, state):
        client, csrf = admin_client
        self._zone(client, csrf)
        post(client, "/puertas/kioscos", csrf, name="Entrada", zone_id=1)
        assert "zone_in_use" in post(client, "/puertas/zonas/1/borrar", csrf).headers["location"]
        assert (
            "kiosk_deleted" in post(client, "/puertas/kioscos/1/borrar", csrf).headers["location"]
        )
        assert "zone_deleted" in post(client, "/puertas/zonas/1/borrar", csrf).headers["location"]

    def test_duplicate_names_are_conflicts(self, admin_client):
        client, csrf = admin_client
        self._zone(client, csrf)
        assert post(client, "/puertas/zonas", csrf, name="Lab").status_code == 409


class TestReports:
    @pytest.fixture
    def data(self, admin_client, state):
        client, _ = admin_client
        state.clock = lambda: FIXED_NOW
        with state.db() as conn:
            person = seed_person(conn, "=Laura Sanjuán")
            conn.execute("UPDATE people SET group_name = 'Monitores'")
            common = {
                "kiosk_id": None,
                "zone_id": None,
                "person_id": person,
                "method": "face",
                "reason": "ok",
            }
            key = state.keys.chain_key
            # 08:00 y 17:30 en Bogotá (UTC-5)
            ledger.record_event(
                conn, key, **common, outcome="granted", when=FIXED_NOW.replace(hour=13)
            )
            ledger.record_event(
                conn, key, **common, outcome="granted", when=FIXED_NOW.replace(hour=22, minute=30)
            )
            ledger.record_event(
                conn,
                key,
                **{**common, "reason": "no_grant"},
                outcome="denied",
                when=FIXED_NOW.replace(hour=14),
            )
        return client

    def test_attendance_uses_local_time_and_ignores_denials(self, data):
        page = data.get("/asistencia", params={"desde": "2026-03-04", "hasta": "2026-03-04"}).text
        assert "08:00" in page and "17:30" in page and "9.5" in page

    def test_late_night_utc_counts_on_local_day(self, state):
        from portero.reports import attendance

        with state.db() as conn:
            person = seed_person(conn, "Óscar Claro")
            # 02:00 UTC del día 5 son las 21:00 del día 4 en Bogotá.
            ledger.record_event(
                conn,
                state.keys.chain_key,
                kiosk_id=None,
                zone_id=None,
                person_id=person,
                method="pin",
                outcome="granted",
                reason="ok_pin",
                when=FIXED_NOW.replace(day=5, hour=2),
            )
            rows = attendance(conn, state.settings.tz, FIXED_NOW.date(), FIXED_NOW.date())
        assert len(rows) == 1 and rows[0]["first"].hour == 21

    def test_csv_exports_are_safe_and_audited(self, data, state):
        params = {"desde": "2026-03-04", "hasta": "2026-03-04"}
        attendance = data.get("/asistencia.csv", params=params)
        assert attendance.headers["content-type"].startswith("text/csv")
        assert "'=Laura" in attendance.text and "9,5" in attendance.text
        events = data.get("/eventos.csv", params=params)
        assert "'=Laura" in events.text and "Concedido" in events.text
        with state.db() as conn:
            actions = {r[0] for r in conn.execute("SELECT action FROM audit_log")}
        assert {"events.export", "attendance.export"} <= actions

    def test_event_filters(self, data):
        params = {"desde": "2026-03-04", "hasta": "2026-03-04", "resultado": "denied"}
        page = data.get("/eventos", params=params).text
        assert "Sin permiso para esta zona" in page and "Acceso autorizado" not in page

    def test_invalid_dates_fall_back(self, data):
        assert data.get("/eventos", params={"desde": "ayer"}).status_code == 200

    def test_dashboard_live_endpoint(self, data):
        rows = data.get("/api/eventos/recientes", params={"desde": 0}).json()
        assert len(rows) == 3 and rows[0]["id"] == 3
        assert data.get("/api/eventos/recientes", params={"desde": 3}).json() == []

    def test_dashboard_renders_chart_and_counts(self, data):
        page = data.get("/").text
        assert "<svg" in page and "accesos concedidos" in page

    def test_dashboard_warns_about_attack_patterns(self, data, state):
        with state.db() as conn:
            for _ in range(5):
                ledger.record_event(
                    conn,
                    state.keys.chain_key,
                    kiosk_id=None,
                    zone_id=None,
                    person_id=None,
                    method="face",
                    outcome="denied",
                    reason="liveness_failed",
                    when=FIXED_NOW,
                )
        assert "rechazos en la última hora" in data.get("/").text

    def test_audit_page_flags_tampering(self, data, state):
        assert "íntegros" in data.get("/bitacora").text
        with state.db() as conn:
            conn.execute("UPDATE events SET outcome = 'granted' WHERE reason = 'no_grant'")
        assert "alterados en la fila" in data.get("/bitacora").text
