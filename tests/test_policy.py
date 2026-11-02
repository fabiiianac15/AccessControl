from datetime import date, datetime

import pytest

from portero.policy import ALL_WEEK, Grant, evaluate, minutes_label, weekdays_label

WEEKDAYS = 0b0011111
MONDAY_10AM = datetime(2026, 3, 2, 10, 0)
SATURDAY_10AM = datetime(2026, 3, 7, 10, 0)


def office(**overrides) -> Grant:
    return Grant(
        **{"zone_id": 1, "weekdays": WEEKDAYS, "start_minute": 480, "end_minute": 1020, **overrides}
    )


def test_inactive_person_is_denied_even_with_a_grant():
    assert evaluate(False, [office()], 1, MONDAY_10AM) == "inactive"


def test_grant_for_another_zone_does_not_count():
    assert evaluate(True, [office(zone_id=2)], 1, MONDAY_10AM) == "no_grant"


def test_inside_schedule_is_allowed():
    assert evaluate(True, [office()], 1, MONDAY_10AM) == "ok"


@pytest.mark.parametrize(
    "moment",
    [datetime(2026, 3, 2, 7, 59), datetime(2026, 3, 2, 17, 0), SATURDAY_10AM],
)
def test_outside_schedule_is_denied(moment):
    assert evaluate(True, [office()], 1, moment) == "outside_schedule"


def test_end_minute_is_exclusive_and_start_inclusive():
    assert evaluate(True, [office()], 1, datetime(2026, 3, 2, 8, 0)) == "ok"
    assert evaluate(True, [office()], 1, datetime(2026, 3, 2, 16, 59)) == "ok"


def test_full_day_grant_covers_last_minute():
    grant = Grant(zone_id=1)
    assert evaluate(True, [grant], 1, datetime(2026, 3, 2, 23, 59)) == "ok"


def test_expired_visitor_is_denied_on_the_next_day_only():
    visitor = Grant(zone_id=1, valid_until=date(2026, 3, 2))
    assert evaluate(True, [visitor], 1, MONDAY_10AM) == "ok"
    assert evaluate(True, [visitor], 1, datetime(2026, 3, 3, 0, 1)) == "expired"


def test_grant_not_started_yet():
    assert (
        evaluate(True, [Grant(zone_id=1, valid_from=date(2026, 3, 3))], 1, MONDAY_10AM)
        == "not_started"
    )


def test_any_valid_grant_wins_over_expired_one():
    grants = [Grant(zone_id=1, valid_until=date(2020, 1, 1)), office()]
    assert evaluate(True, grants, 1, MONDAY_10AM) == "ok"


class TestOvernightShift:
    # Turno de 22:00 a 06:00 que solo se autoriza empezar el viernes.
    friday_night = Grant(zone_id=1, weekdays=1 << 4, start_minute=1320, end_minute=360)

    def test_evening_part_uses_the_day_it_starts(self):
        assert evaluate(True, [self.friday_night], 1, datetime(2026, 3, 6, 23, 0)) == "ok"

    def test_early_morning_belongs_to_the_previous_day(self):
        assert evaluate(True, [self.friday_night], 1, datetime(2026, 3, 7, 5, 59)) == "ok"

    def test_thursday_night_is_not_covered(self):
        assert (
            evaluate(True, [self.friday_night], 1, datetime(2026, 3, 5, 23, 0))
            == "outside_schedule"
        )

    def test_friday_early_morning_is_not_covered(self):
        assert (
            evaluate(True, [self.friday_night], 1, datetime(2026, 3, 6, 3, 0)) == "outside_schedule"
        )

    def test_midday_gap_is_outside(self):
        assert (
            evaluate(True, [self.friday_night], 1, datetime(2026, 3, 6, 12, 0))
            == "outside_schedule"
        )

    def test_shift_started_on_last_valid_day_may_finish_after_midnight(self):
        grant = Grant(
            zone_id=1,
            weekdays=ALL_WEEK,
            start_minute=1320,
            end_minute=360,
            valid_until=date(2026, 3, 6),
        )
        assert evaluate(True, [grant], 1, datetime(2026, 3, 7, 5, 0)) == "ok"
        assert evaluate(True, [grant], 1, datetime(2026, 3, 7, 23, 0)) == "expired"


def test_labels():
    assert weekdays_label(ALL_WEEK) == "Todos los días"
    assert weekdays_label(WEEKDAYS) == "Lun a Vie"
    assert weekdays_label(0b1000001) == "Lun Dom"
    assert minutes_label(1440) == "24:00"
    assert minutes_label(495) == "08:15"
