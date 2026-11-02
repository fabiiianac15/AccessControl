"""Recorridos completos del kiosco por HTTP, con un motor facial guionizado."""

import random

import pytest

from conftest import enroll, face, grant_all, near, seed_person, seed_zone_and_kiosk, unit
from portero import kiosk_flow
from portero.biometrics.liveness import CENTER, LEFT
from portero.kiosk_flow import KioskFlow

LAURA = unit(1)
STRANGER = unit(2)
TURN = {"left": 0.35, "right": -0.35, CENTER: 0.0}


class Kiosk:
    def __init__(self, client, engine, token, frame):
        self.client = client
        self.engine = engine
        self.headers = {"Authorization": f"Bearer {token}"}
        self.frame = frame

    def send(self, yaw=0.0, embedding=LAURA, faces=None):
        self.engine.queue(faces if faces is not None else [face(yaw)], embedding)
        response = self.client.post("/api/kiosk/v1/frame", content=self.frame, headers=self.headers)
        assert response.status_code == 200, response.text
        return response.json()

    def complete_challenge(self, first):
        state = first
        for _ in range(12):
            if state["phase"] != "challenge":
                return state
            state = self.send(TURN[state["direction"]])
        return state


@pytest.fixture
def clock():
    class Clock:
        now = 1000.0

        def __call__(self):
            return self.now

    return Clock()


@pytest.fixture
def setup(app, state, client, engine, frame_bytes, clock, request):
    app.state.flow = KioskFlow(state, monotonic=clock, rng=random.Random(5))
    liveness = getattr(request, "param", True)
    with state.db() as conn:
        zone, token = seed_zone_and_kiosk(state, conn, liveness=liveness)
        person = seed_person(conn, "Laura Sanjuán")
        enroll(state, conn, person, LAURA)
        grant_all(conn, person, zone)
    return Kiosk(client, engine, token, frame_bytes), person, zone


def events(state):
    with state.db() as conn:
        return conn.execute("SELECT * FROM events ORDER BY id").fetchall()


def test_frame_requires_device_token(client, frame_bytes):
    assert client.post("/api/kiosk/v1/frame", content=frame_bytes).status_code == 401
    bad = {"Authorization": "Bearer inventado"}
    assert client.post("/api/kiosk/v1/frame", content=frame_bytes, headers=bad).status_code == 401


def test_inactive_kiosk_token_stops_working(setup, state, frame_bytes):
    kiosk, _, _ = setup
    with state.db() as conn:
        conn.execute("UPDATE kiosks SET active = 0")
    response = kiosk.client.post("/api/kiosk/v1/frame", content=frame_bytes, headers=kiosk.headers)
    assert response.status_code == 401


def test_corrupt_frame_is_rejected_without_opening_anything(setup, state):
    kiosk, _, _ = setup
    response = kiosk.client.post("/api/kiosk/v1/frame", content=b"basura", headers=kiosk.headers)
    assert response.status_code == 422
    assert events(state) == []


def test_oversized_frame_is_rejected(setup, settings):
    kiosk, _, _ = setup
    big = b"\0" * (settings.max_frame_bytes + 128 * 1024)
    response = kiosk.client.post("/api/kiosk/v1/frame", content=big, headers=kiosk.headers)
    assert response.status_code == 413


def test_no_face_gives_guidance(setup):
    kiosk, _, _ = setup
    assert kiosk.send(faces=[])["hint"] == "no_face"


def test_two_people_are_refused(setup):
    kiosk, _, _ = setup
    state = kiosk.send(faces=[face(), face(box=(20.0, 20.0, 140.0, 180.0))])
    assert state["hint"] == "one_person"


def test_distant_passerby_does_not_block(setup):
    kiosk, _, _ = setup
    state = kiosk.send(faces=[face(), face(box=(10.0, 10.0, 40.0, 50.0))])
    assert state["hint"] != "one_person"


def test_full_flow_grants_access(setup, state):
    kiosk, person, _ = setup
    assert kiosk.send()["phase"] == "guide"  # primer cuadro: confirma identidad
    result = kiosk.complete_challenge(kiosk.send())
    assert result["phase"] == "result"
    assert result["granted"] is True
    assert result["name"] == "Laura"  # solo el primer nombre en pantalla pública
    row = events(state)[-1]
    assert (row["outcome"], row["person_id"], row["method"]) == ("granted", person, "face")


def test_static_photo_times_out(setup, state, clock):
    kiosk, _, _ = setup
    kiosk.send()
    assert kiosk.send()["phase"] == "challenge"
    for _ in range(30):
        clock.now += 1
        result = kiosk.send(0.0)
        if result["phase"] == "result":
            break
    assert result["granted"] is False
    assert result["reason"] == "liveness_failed"
    assert result["name"] is None  # una foto no debe revelar de quién es
    assert events(state)[-1]["reason"] == "liveness_failed"


def test_swapping_person_during_challenge_is_denied(setup, state):
    kiosk, _, _ = setup
    kiosk.send()
    state_view = kiosk.send()
    assert state_view["phase"] == "challenge"
    for _ in range(kiosk_flow.CONTINUITY_MAX_MISSES - 1):
        assert kiosk.send(TURN[state_view["direction"]], embedding=STRANGER)["phase"] == "challenge"
    result = kiosk.send(TURN[state_view["direction"]], embedding=STRANGER)
    assert result["reason"] == "identity_changed"
    assert result["granted"] is False and result["name"] is None
    assert events(state)[-1]["outcome"] == "denied"


def test_blurry_turn_frame_is_tolerated(setup):
    kiosk, _, _ = setup
    kiosk.send()
    first = kiosk.send()
    kiosk.send(TURN[first["direction"]], embedding=STRANGER)  # un solo cuadro extraño
    result = kiosk.complete_challenge(kiosk.send(TURN[first["direction"]]))
    assert result["granted"] is True


def test_final_frontal_frame_must_reach_full_threshold(setup, state, clock):
    """Pasa la continuidad laxa con 0.3, pero no puede terminar la prueba con esa similitud."""
    kiosk, _, _ = setup
    weak = near(LAURA, 0.3)
    kiosk.send()
    view = kiosk.send()
    for _ in range(30):
        view = kiosk.send(TURN[view["direction"]], embedding=weak)
        clock.now += 1
        if view["phase"] == "result":
            break
    assert view["granted"] is False
    assert view["reason"] == "liveness_failed"


def test_unknown_face_is_denied_after_several_frames(setup, state):
    kiosk, _, _ = setup
    for _ in range(kiosk_flow.UNKNOWN_FRAMES - 1):
        assert kiosk.send(embedding=STRANGER)["phase"] == "guide"
    result = kiosk.send(embedding=STRANGER)
    assert result["granted"] is False and result["reason"] == "unknown_face"
    row = events(state)[-1]
    assert row["person_id"] is None and row["score"] < 0.45


def test_result_holds_then_clears_without_duplicate_events(setup, state, clock):
    kiosk, _, _ = setup
    kiosk.send()
    kiosk.complete_challenge(kiosk.send())
    total = len(events(state))
    assert kiosk.send()["phase"] == "result"  # sigue mostrando, sin registrar otro evento
    assert len(events(state)) == total
    clock.now += kiosk_flow.RESULT_SECONDS + 0.1
    assert kiosk.send()["phase"] == "guide"


@pytest.mark.parametrize("setup", [False], indirect=True)
def test_kiosk_without_liveness_grants_directly(setup):
    kiosk, _, _ = setup
    kiosk.send()
    assert kiosk.send()["granted"] is True


def test_recognized_person_without_grant_is_denied_after_proving_presence(setup, state):
    kiosk, person, _ = setup
    with state.db() as conn:
        conn.execute("DELETE FROM grants WHERE person_id = ?", (person,))
    kiosk.send()
    result = kiosk.complete_challenge(kiosk.send())
    assert result["granted"] is False and result["reason"] == "no_grant"
    assert result["name"] == "Laura"


def test_engine_failure_fails_closed(setup, state, engine):
    kiosk, _, _ = setup
    kiosk.send()
    kiosk.send()  # prueba en curso

    def explode(_image):
        raise RuntimeError("fallo del modelo")

    engine.detect = explode
    client = kiosk.client
    client_no_raise = type(client)(client.app, raise_server_exceptions=False)
    response = client_no_raise.post(
        "/api/kiosk/v1/frame", content=kiosk.frame, headers=kiosk.headers
    )
    assert response.status_code == 500
    assert all(row["outcome"] != "granted" for row in events(state))
    session = client.app.state.flow.session(1)
    assert session.challenge is None


class TestDoor:
    @pytest.fixture
    def door_kiosk(self, app, state, client, engine, frame_bytes, clock):
        app.state.flow = KioskFlow(state, monotonic=clock, rng=random.Random(5))
        with state.db() as conn:
            zone, token = seed_zone_and_kiosk(
                state, conn, liveness=False, webhook="http://puerta.local/abrir"
            )
            person = seed_person(conn, "Laura Sanjuán")
            enroll(state, conn, person, LAURA)
            grant_all(conn, person, zone)
        return Kiosk(client, engine, token, frame_bytes), person

    def test_granted_opens_door_with_decrypted_secret(self, door_kiosk, door, state):
        kiosk, _ = door_kiosk
        kiosk.send()
        assert kiosk.send()["door"] == "opened"
        assert door.calls[0]["secret"] == "secreto-puerta"
        assert door.calls[0]["payload"]["event"] == events(state)[-1]["id"]
        assert events(state)[-1]["door_status"] == "opened"

    def test_denied_never_calls_the_door(self, door_kiosk, door, state):
        kiosk, person = door_kiosk
        with state.db() as conn:
            conn.execute("DELETE FROM grants WHERE person_id = ?", (person,))
        kiosk.send()
        assert kiosk.send()["granted"] is False
        assert door.calls == []

    def test_door_failure_is_reported_and_logged(self, door_kiosk, door, state):
        door.result = "failed"
        kiosk, _ = door_kiosk
        kiosk.send()
        result = kiosk.send()
        assert result["granted"] is True and result["door"] == "failed"
        assert events(state)[-1]["door_status"] == "failed"

    def test_if_logging_fails_the_door_stays_closed(self, door_kiosk, door, monkeypatch):
        kiosk, _ = door_kiosk

        def broken(*_args, **_kwargs):
            raise OSError("disco lleno")

        monkeypatch.setattr("portero.ledger.record_event", broken)
        kiosk.send()
        kiosk.engine.queue([face()], LAURA)
        safe = type(kiosk.client)(kiosk.client.app, raise_server_exceptions=False)
        response = safe.post("/api/kiosk/v1/frame", content=kiosk.frame, headers=kiosk.headers)
        assert response.status_code == 500
        assert door.calls == []


class TestPin:
    @pytest.fixture
    def pin_kiosk(self, setup, state):
        kiosk, person, _ = setup
        from portero.people import assign_pin

        with state.db() as conn:
            pin = assign_pin(state, conn, person)
        return kiosk, person, pin

    def submit(self, kiosk, pin):
        return kiosk.client.post("/api/kiosk/v1/pin", json={"pin": pin}, headers=kiosk.headers)

    def wrong(self, pin):
        return "000001" if pin != "000001" else "000002"

    def test_correct_pin_grants_without_camera(self, pin_kiosk, state):
        kiosk, person, pin = pin_kiosk
        result = self.submit(kiosk, pin).json()
        assert result["granted"] is True and result["reason"] == "ok_pin"
        row = events(state)[-1]
        assert (row["method"], row["person_id"]) == ("pin", person)

    def test_pin_still_obeys_policy(self, pin_kiosk, state):
        kiosk, person, pin = pin_kiosk
        with state.db() as conn:
            conn.execute("DELETE FROM grants WHERE person_id = ?", (person,))
        result = self.submit(kiosk, pin).json()
        assert result["granted"] is False and result["reason"] == "no_grant"

    def test_wrong_pin_is_denied_and_logged(self, pin_kiosk, state):
        kiosk, _, pin = pin_kiosk
        result = self.submit(kiosk, self.wrong(pin)).json()
        assert result["granted"] is False and result["reason"] == "pin_invalid"
        assert events(state)[-1]["reason"] == "pin_invalid"

    def test_lockouts_escalate_and_valid_pin_does_not_reset_them(self, pin_kiosk, settings, clock):
        kiosk, _, pin = pin_kiosk
        session = kiosk.client.app.state.flow.session(1)

        def fail_until_locked():
            for _ in range(settings.pin_max_failures):
                clock.now += 5
                self.submit(kiosk, self.wrong(pin))
            return session.pin_locked_until - clock.now

        assert fail_until_locked() == pytest.approx(settings.pin_lockout_seconds)
        clock.now += settings.pin_lockout_seconds + 1
        assert self.submit(kiosk, pin).json()["granted"] is True  # alguien entra con su PIN
        clock.now += 5
        assert fail_until_locked() == pytest.approx(settings.pin_lockout_seconds * 2)
        clock.now += settings.pin_lockout_seconds * 2 + 1
        assert fail_until_locked() == pytest.approx(settings.pin_lockout_seconds * 4)

    def test_lockout_never_exceeds_the_cap(self, pin_kiosk, settings, clock):
        kiosk, _, pin = pin_kiosk
        session = kiosk.client.app.state.flow.session(1)
        session.pin_lockouts = 30
        session.pin_last_failure = clock.now
        for _ in range(settings.pin_max_failures):
            clock.now += 5
            self.submit(kiosk, self.wrong(pin))
        assert session.pin_locked_until - clock.now == pytest.approx(
            settings.pin_lockout_max_seconds
        )

    def test_failures_are_forgotten_after_a_quiet_period(self, pin_kiosk, clock):
        kiosk, _, pin = pin_kiosk
        session = kiosk.client.app.state.flow.session(1)
        session.pin_lockouts = 3
        session.pin_failures = 4
        session.pin_last_failure = clock.now
        clock.now += kiosk_flow.PIN_FORGET_SECONDS + 1
        self.submit(kiosk, self.wrong(pin))
        assert (session.pin_failures, session.pin_lockouts) == (1, 0)

    def test_brute_force_locks_the_kiosk(self, pin_kiosk, settings, clock):
        kiosk, _, pin = pin_kiosk
        for _ in range(settings.pin_max_failures):
            clock.now += 5  # deja pasar la pantalla de resultado
            last = self.submit(kiosk, self.wrong(pin)).json()
        assert last["reason"] == "pin_locked"
        # Ni el PIN correcto funciona durante el bloqueo.
        locked = self.submit(kiosk, pin).json()
        assert locked["phase"] == "pin_locked"
        clock.now += settings.pin_lockout_seconds + 1
        assert self.submit(kiosk, pin).json()["granted"] is True

    @pytest.mark.parametrize("value", ["123", "abcdef", "1234567", ""])
    def test_malformed_pin_rejected(self, pin_kiosk, value):
        kiosk, _, _ = pin_kiosk
        assert self.submit(kiosk, value).status_code == 422

    def test_kiosk_can_disable_pin(self, pin_kiosk, state):
        kiosk, _, pin = pin_kiosk
        with state.db() as conn:
            conn.execute("UPDATE kiosks SET allow_pin = 0")
        assert self.submit(kiosk, pin).status_code == 403


def test_challenge_uses_requested_order(setup):
    kiosk, _, _ = setup
    kiosk.send()
    assert kiosk.send()["direction"] in {LEFT, "right"}


def test_denied_photo_only_stored_when_enabled(
    app, state, settings, client, engine, frame_bytes, clock
):
    app.state.flow = KioskFlow(state, monotonic=clock, rng=random.Random(5))
    with state.db() as conn:
        _, token = seed_zone_and_kiosk(state, conn)
        person = seed_person(conn, "Laura Sanjuán")
        enroll(state, conn, person, LAURA)
    kiosk = Kiosk(client, engine, token, frame_bytes)

    for _ in range(kiosk_flow.UNKNOWN_FRAMES):
        kiosk.send(embedding=STRANGER)
    assert events(state)[-1]["photo_file"] is None
    assert not settings.photos_dir.exists()

    settings.store_denied_photos = True
    clock.now += kiosk_flow.RESULT_SECONDS + 1
    for _ in range(kiosk_flow.UNKNOWN_FRAMES):
        kiosk.send(embedding=STRANGER)
    name = events(state)[-1]["photo_file"]
    stored = (settings.photos_dir / name).read_bytes()
    assert not stored.startswith(b"\xff\xd8")  # no queda como JPEG legible en disco
    assert state.keys.decrypt(stored, f"photo:{name}").startswith(b"\xff\xd8")
