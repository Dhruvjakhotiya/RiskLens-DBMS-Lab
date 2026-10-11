from datetime import datetime, timezone

from time_utils import format_ist, to_ist


def test_utc_timestamp_converts_to_ist():
    converted = to_ist("2026-10-11T10:06:00+00:00")
    assert converted.isoformat() == "2026-10-11T15:36:00+05:30"


def test_naive_sqlite_utc_timestamp_rolls_over_date_boundary():
    assert format_ist("2026-10-11 23:45:00") == "12 Oct 2026, 05:15:00 IST"


def test_already_localized_timestamp_is_not_shifted_twice():
    localized = datetime(2026, 10, 11, 15, 36, tzinfo=timezone.utc).astimezone(
        timezone.utc
    ).isoformat()
    assert format_ist(localized) == "11 Oct 2026, 21:06:00 IST"
    assert format_ist("2026-10-11T15:36:00+05:30") == "11 Oct 2026, 15:36:00 IST"
