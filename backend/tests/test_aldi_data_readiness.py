import pandas as pd

from backend.app.data_readiness import count_consecutive_windows, build_readiness


def test_counts_one_complete_7_plus_7_training_window():
    dates = pd.date_range("2026-01-01", periods=14, freq="D")
    daily = pd.DataFrame({"respondent_id": ["R1"] * 14, "date": dates})
    sessions = pd.DataFrame({
        "respondent_id": ["R1"] * 14, "date": dates,
        "sbp_mean": [120.0] * 14, "dbp_mean": [80.0] * 14,
    })
    result = count_consecutive_windows(daily, sessions)
    assert result == {
        "history_7d_respondents": 1,
        "training_windows_7d": 1,
        "training_window_respondents": 1,
    }


def test_missing_calendar_day_breaks_training_window():
    dates = pd.date_range("2026-01-01", periods=14, freq="D").delete(8)
    daily = pd.DataFrame({"respondent_id": ["R1"] * len(dates), "date": dates})
    sessions = pd.DataFrame({
        "respondent_id": ["R1"] * len(dates), "date": dates,
        "sbp_mean": [120.0] * len(dates), "dbp_mean": [80.0] * len(dates),
    })
    result = count_consecutive_windows(daily, sessions)
    assert result["training_windows_7d"] == 0


def test_pending_bp_session_does_not_count_as_valid_window():
    dates = pd.date_range("2026-01-01", periods=14, freq="D")
    daily = pd.DataFrame({"respondent_id": ["R1"] * 14, "date": dates})
    sessions = pd.DataFrame({
        "respondent_id": ["R1"] * 14, "date": dates,
        "sbp_mean": [120.0] * 13 + [None], "dbp_mean": [80.0] * 13 + [None],
    })
    result = count_consecutive_windows(daily, sessions)
    assert result["training_windows_7d"] == 0


def test_readiness_marks_synthetic_as_technical_only():
    profiles = pd.DataFrame({"respondent_id": ["SIM001"]})
    daily = pd.DataFrame({
        "respondent_id": ["SIM001"], "date": [pd.Timestamp("2026-01-01")],
        "sleep_hours": [None], "sitting": [None],
    })
    sessions = pd.DataFrame({"respondent_id": ["SIM001"], "date": [pd.Timestamp("2026-01-01")], "sbp_mean": [120.0], "dbp_mean": [80.0]})
    result = build_readiness(profiles, sessions, daily, {}, "synthetic")
    assert result["ml_status"] == "synthetic_technical_check_only"
    assert result["sleep_missing"] == 1
