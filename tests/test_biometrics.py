import random

import cv2
import numpy as np
import pytest

from conftest import FIXTURES, face, landmarks, near, unit
from portero.biometrics.engine import Face, OpenCVFaceEngine, decode_image
from portero.biometrics.gallery import Gallery, template_context
from portero.biometrics.liveness import (
    CENTER,
    LEFT,
    RIGHT,
    Challenge,
    ChallengeStatus,
    face_aspect,
    yaw_ratio,
)
from portero.biometrics.quality import assess


class TestYaw:
    def test_frontal_is_zero(self):
        assert yaw_ratio(landmarks(0.0)) == pytest.approx(0.0, abs=1e-5)

    def test_sign(self):
        assert yaw_ratio(landmarks(0.3)) == pytest.approx(0.3, abs=1e-5)
        assert yaw_ratio(landmarks(-0.3)) == pytest.approx(-0.3, abs=1e-5)

    def test_rolling_the_head_does_not_look_like_a_turn(self):
        angle = np.radians(25)
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        rolled = (landmarks(0.0) - [320, 240]) @ rotation.T + [320, 240]
        assert abs(yaw_ratio(rolled.astype(np.float32))) < 0.01

    def test_degenerate_points_do_not_crash(self):
        assert yaw_ratio(np.zeros((5, 2), dtype=np.float32)) == 0.0


def drive(challenge: Challenge, yaw: float, frames: int = 2, start: float = 1.0) -> ChallengeStatus:
    status = ChallengeStatus.RUNNING
    for index in range(frames):
        status = challenge.feed(landmarks(yaw), start + index * 0.1)
    return status


BASE = face_aspect(landmarks())
YAW_FOR = {LEFT: 0.35, RIGHT: -0.35, CENTER: 0.0}


class TestChallenge:
    def test_always_requires_both_directions(self):
        for seed in range(40):
            steps = Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(seed)).steps
            assert steps[1] == steps[3] == CENTER
            assert {steps[0], steps[2]} == {LEFT, RIGHT}

    def test_both_orders_occur(self):
        seen = {
            tuple(Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(i)).steps)
            for i in range(60)
        }
        assert len(seen) == 2

    def test_following_the_prompts_passes(self):
        challenge = Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(2))
        status = ChallengeStatus.RUNNING
        for step in list(challenge.steps):
            status = drive(challenge, YAW_FOR[step])
        assert status is ChallengeStatus.PASSED

    def test_static_face_never_passes(self):
        challenge = Challenge(started_at=0, baseline_aspect=BASE, timeout=5, rng=random.Random(2))
        assert drive(challenge, 0.0, frames=40) is ChallengeStatus.RUNNING
        assert challenge.position == 0

    def test_wrong_direction_does_not_advance(self):
        challenge = Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(2))
        wrong = RIGHT if challenge.current == LEFT else LEFT
        drive(challenge, YAW_FOR[wrong], frames=6)
        assert challenge.position == 0

    def test_single_frame_spike_is_not_enough(self):
        challenge = Challenge(
            started_at=0, baseline_aspect=BASE, hold_frames=2, rng=random.Random(2)
        )
        drive(challenge, YAW_FOR[challenge.current], frames=1)
        drive(challenge, 0.0, frames=1)
        drive(challenge, YAW_FOR[challenge.current], frames=1)
        assert challenge.position == 0

    def test_tilted_flat_photo_fails_on_foreshortening(self):
        """La nariz parece moverse, pero los ojos se juntan como solo pasa al inclinar un plano."""
        challenge = Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(2))
        yaw = YAW_FOR[challenge.current]
        squeezed = landmarks(yaw, eye_distance=80 * 0.5)
        for index in range(6):
            challenge.feed(squeezed, 1 + index * 0.1)
        assert challenge.position == 0
        assert challenge.overturned is True

    def test_real_turn_with_mild_foreshortening_passes(self):
        challenge = Challenge(started_at=0, baseline_aspect=BASE, rng=random.Random(2))
        yaw = YAW_FOR[challenge.current]
        for index in range(2):
            challenge.feed(landmarks(yaw, eye_distance=80 * 0.8), 1 + index * 0.1)
        assert challenge.position == 1

    def test_timeout(self):
        challenge = Challenge(started_at=0, baseline_aspect=BASE, timeout=5, rng=random.Random(2))
        assert challenge.feed(landmarks(0.0), now=5.1) is ChallengeStatus.TIMED_OUT


class TestGallery:
    def _gallery(self, conn, state, **owners) -> Gallery:
        from conftest import enroll, seed_person

        ids = {}
        for name, vector in owners.items():
            ids[name] = seed_person(conn, name)
            enroll(state, conn, ids[name], vector)
        gallery = Gallery(0.45, 0.05)
        gallery.reload(conn, state.keys)
        return gallery, ids

    def test_returns_the_closest_person_not_the_first(self, conn, state):
        # El sistema anterior elegía el primer registro bajo tolerancia: una suplantación directa.
        ana = unit(1)
        gallery, ids = self._gallery(conn, state, Yeimy=near(ana, 0.5), Laura=ana)
        match = gallery.match(ana)
        assert match.person_id == ids["Laura"]

    def test_below_threshold_is_rejected(self, conn, state):
        ana = unit(1)
        gallery, _ = self._gallery(conn, state, Laura=ana)
        assert gallery.match(near(ana, 0.40)).person_id is None
        assert gallery.match(near(ana, 0.50)).person_id is not None

    def test_ambiguous_match_is_rejected(self, conn, state):
        ana = unit(1)
        gallery, _ = self._gallery(conn, state, Laura=ana, Natalia=near(ana, 0.98))
        match = gallery.match(ana)
        assert match.person_id is None and match.score == pytest.approx(1.0)

    def test_samples_of_the_same_person_are_not_competitors(self, conn, state):
        from conftest import enroll, seed_person

        ana = unit(1)
        person = seed_person(conn, "Laura")
        enroll(state, conn, person, ana)
        enroll(state, conn, person, near(ana, 0.99))
        gallery = Gallery(0.45, 0.05)
        gallery.reload(conn, state.keys)
        assert gallery.match(ana).person_id == person

    def test_empty_gallery(self):
        assert Gallery(0.45, 0.05).match(unit(1)).person_id is None

    def test_excludes_people_without_consent_or_inactive(self, conn, state):
        from conftest import enroll, seed_person

        with_consent = seed_person(conn, "Laura")
        no_consent = seed_person(conn, "Diego", consent=False)
        inactive = seed_person(conn, "Karen")
        for person, seed in ((with_consent, 1), (no_consent, 2), (inactive, 3)):
            enroll(state, conn, person, unit(seed))
        conn.execute("UPDATE people SET active = 0 WHERE id = ?", (inactive,))
        gallery = Gallery(0.45, 0.05)
        gallery.reload(conn, state.keys)
        assert gallery.size() == 1
        assert gallery.best(unit(2))[0] == with_consent

    def test_template_is_encrypted_at_rest(self, conn, state):
        from conftest import enroll, seed_person

        vector = unit(1)
        person = seed_person(conn, "Laura")
        enroll(state, conn, person, vector)
        stored = conn.execute("SELECT ciphertext FROM templates").fetchone()[0]
        assert vector.tobytes() not in stored
        assert state.keys.decrypt(stored, template_context(person)).startswith(vector.tobytes())


class TestQuality:
    def _image(self, level=128, noise=50):
        rng = np.random.default_rng(1)
        low, high = max(level - noise, 0), min(level + noise, 255)
        return rng.integers(low, high + 1, size=(480, 640, 3), dtype=np.uint8)

    def test_good_frame(self):
        result = assess(self._image(), face())
        assert result.ok and 0 < result.score <= 1

    def test_small_face(self):
        small = Face(box=(300, 200, 40, 50), landmarks=landmarks(0, eye_distance=20), score=0.9)
        assert assess(self._image(), small).issue == "too_small"

    def test_cut_by_the_frame(self):
        assert assess(self._image(), face(box=(600.0, 150.0, 160.0, 200.0))).issue == "off_frame"

    def test_too_dark(self):
        assert assess(self._image(level=25, noise=20), face()).issue == "too_dark"

    def test_too_bright(self):
        assert assess(self._image(level=240, noise=10), face()).issue == "too_bright"

    def test_blurry(self):
        blurred = cv2.GaussianBlur(self._image(), (31, 31), 0)
        assert assess(blurred, face()).issue == "blurry"

    def test_not_frontal(self):
        assert assess(self._image(), face(yaw=0.3)).issue == "not_frontal"


class TestDecode:
    @pytest.mark.parametrize("data", [b"", b"no soy una imagen", b"\xff\xd8\xff\xe0" + b"\0" * 40])
    def test_garbage_returns_none(self, data):
        assert decode_image(data) is None

    def test_large_image_is_scaled_down(self):
        _, encoded = cv2.imencode(".png", np.zeros((3000, 4000, 3), dtype=np.uint8))
        assert max(decode_image(encoded.tobytes()).shape[:2]) == 1280


@pytest.fixture(scope="module")
def real_engine(real_models):
    return OpenCVFaceEngine(real_models)


@pytest.mark.models
class TestRealModels:
    @staticmethod
    def _load(name):
        image = cv2.imread(str(FIXTURES / name))
        assert image is not None, name
        return image

    def _embedding(self, engine, image):
        faces = engine.detect(image)
        assert faces, "no detectó el rostro"
        return engine.embed(image, faces[0])

    def test_same_photo_with_changes_matches_and_different_people_do_not(self, real_engine):
        collins = self._load("collins.jpg")
        armstrong = self._load("armstrong.jpg")
        reference = self._embedding(real_engine, collins)
        altered = cv2.convertScaleAbs(cv2.flip(collins, 1), alpha=0.85, beta=8)
        assert reference @ self._embedding(real_engine, altered) > 0.45
        assert reference @ self._embedding(real_engine, armstrong) < 0.45

    def test_landscape_without_face_is_not_detected(self, real_engine):
        gradient = np.tile(np.linspace(0, 255, 640, dtype=np.uint8), (480, 1))
        assert real_engine.detect(cv2.merge([gradient] * 3)) == []

    @pytest.mark.parametrize("name", ["collins.jpg", "armstrong.jpg", "aldrin.jpg"])
    def test_tilting_a_flat_photo_cannot_turn_both_ways(self, real_engine, name):
        """El ataque común: mostrar una foto e inclinarla para imitar los giros."""
        image = self._load(name)
        height, width = image.shape[:2]
        frontal = real_engine.detect(image)[0]
        baseline = face_aspect(frontal.landmarks)
        center_x = frontal.box[0] + frontal.box[2] / 2
        center_y = frontal.box[1] + frontal.box[3] / 2
        focal = max(width, height) * 1.2
        corners = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        accepted = set()
        for degrees in (-65, -55, -45, -35, -25, -15, 15, 25, 35, 45, 55, 65):
            theta = np.radians(degrees)
            projected = []
            for x, y in corners:
                depth = focal / (focal + (x - center_x) * np.sin(theta))
                projected.append(
                    [
                        center_x + (x - center_x) * np.cos(theta) * depth,
                        center_y + (y - center_y) * depth,
                    ]
                )
            warp = cv2.getPerspectiveTransform(corners, np.float32(projected))
            tilted = cv2.warpPerspective(image, warp, (width, height))
            for face_found in real_engine.detect(tilted)[:1]:
                for direction in (LEFT, RIGHT):
                    challenge = Challenge(
                        started_at=0, baseline_aspect=baseline, rng=random.Random(0)
                    )
                    challenge.steps[0] = direction
                    if challenge._satisfied(face_found.landmarks):
                        accepted.add(direction)
        assert accepted != {LEFT, RIGHT}
