"""Readiness summaries for the Kelola Data page.

Only aggregate counts and technical readiness metadata are returned. No raw
answers, direct identifiers, or row-level rejection details are exposed.
"""
from collections import Counter
import pandas as pd


def count_consecutive_windows(daily, sessions, history_days=7, target_days=7):
    """Count complete rolling history+target windows per respondent.

    A day is usable only when at least one technically valid BP session exists.
    Windows require every calendar date in both periods; gaps are not bridged.
    """
    if daily.empty or sessions.empty:
        return {"history_7d_respondents": 0, "training_windows_7d": 0,
                "training_window_respondents": 0}
    valid = sessions.dropna(subset=["sbp_mean", "dbp_mean"]).copy()
    if valid.empty:
        return {"history_7d_respondents": 0, "training_windows_7d": 0,
                "training_window_respondents": 0}
    valid["date"] = pd.to_datetime(valid["date"]).dt.normalize()
    daily_dates = daily[["respondent_id", "date"]].drop_duplicates().copy()
    daily_dates["date"] = pd.to_datetime(daily_dates["date"]).dt.normalize()
    usable = valid.groupby(["respondent_id", "date"], as_index=False).agg(
        sbp_mean=("sbp_mean", "mean"))
    usable_dates = set(zip(usable.respondent_id, usable.date))
    history_respondents = set()
    training_respondents = set()
    windows = 0
    for rid, group in daily_dates.groupby("respondent_id"):
        dates = sorted(group.date.unique())
        date_set = set(dates)
        for end_idx, end in enumerate(dates):
            history = [end - pd.Timedelta(days=offset) for offset in range(history_days - 1, -1, -1)]
            if all((rid, day) in usable_dates for day in history):
                history_respondents.add(rid)
            # end is the last history date; target starts the following day.
            target = [end + pd.Timedelta(days=offset) for offset in range(1, target_days + 1)]
            full = history + target
            if all(day in date_set and (rid, day) in usable_dates for day in full):
                windows += 1
                training_respondents.add(rid)
    return {"history_7d_respondents": len(history_respondents),
            "training_windows_7d": windows,
            "training_window_respondents": len(training_respondents)}


def build_readiness(profiles, sessions, daily, quality, source_kind):
    profiles_n = len(profiles)
    daily_n = len(daily)
    session_n = len(sessions)
    valid_sessions = int(sessions.dropna(subset=["sbp_mean", "dbp_mean"]).shape[0]) if session_n else 0
    dates = pd.to_datetime(daily["date"], errors="coerce").dropna() if daily_n else pd.Series(dtype="datetime64[ns]")
    issue_counts = quality.get("issue_counts", {}) if isinstance(quality, dict) else {}
    row_outcomes = quality.get("row_outcomes", {}) if isinstance(quality, dict) else {}
    profile_rows = row_outcomes.get("profiles", {})
    daily_rows = row_outcomes.get("daily", {})
    windows = count_consecutive_windows(daily, sessions)
    actual = source_kind == "actual"
    unresolved = (int(sum(issue_counts.values())) +
                  int(profile_rows.get("quarantined", 0)) +
                  int(daily_rows.get("quarantined", 0)) +
                  int(sessions.get("review_status", pd.Series(dtype=str)).eq("pending_review").sum())
                  if "review_status" in sessions else
                  int(sum(issue_counts.values())) + int(profile_rows.get("quarantined", 0)) +
                  int(daily_rows.get("quarantined", 0)))
    return {
        "source_kind": source_kind,
        "label": "DATA AKTUAL" if actual else "DATA SINTETIS / SIMULASI" if source_kind == "synthetic" else "BELUM ADA DATA",
        "profiles": profiles_n, "daily_records": daily_n, "session_records": session_n,
        "valid_sessions": valid_sessions, "date_count": int(dates.dt.date.nunique()),
        "min_date": str(dates.min().date()) if len(dates) else None,
        "max_date": str(dates.max().date()) if len(dates) else None,
        "profile_quarantined": int(profile_rows.get("quarantined", 0)),
        "daily_quarantined": int(daily_rows.get("quarantined", 0)),
        "issue_count": int(sum(issue_counts.values())),
        "unresolved_session_reviews": int(sessions.get("review_status", pd.Series(dtype=str)).eq("pending_review").sum())
            if "review_status" in sessions else 0,
        "sleep_missing": int(daily["sleep_hours"].isna().sum()) if "sleep_hours" in daily else 0,
        "sitting_missing": int(daily["sitting"].isna().sum()) if "sitting" in daily else 0,
        "training_target": "future_7d_mean_sbp",
        "history_7d_respondents": windows["history_7d_respondents"],
        "training_windows_7d": windows["training_windows_7d"],
        "training_window_respondents": windows["training_window_respondents"],
        "ml_status": "pending_actual_validation" if actual else
                     "synthetic_technical_check_only" if source_kind == "synthetic" else "no_data",
        "ml_note": ("Jumlah window teknis; belum membuktikan kelayakan ilmiah atau persetujuan target."
                    if source_kind in ("actual", "synthetic") else "Belum ada data untuk dihitung."),
    }
