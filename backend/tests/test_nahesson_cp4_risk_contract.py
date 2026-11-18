
"""CP4 contract checks for Nahesson's descriptive risk-analysis page.

These tests intentionally use the repository's labelled synthetic fixture via
``test_cp3_stage1.loaded``. They verify aggregation semantics only; they are not
research findings and do not establish readiness of actual respondent data.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_cp3_stage1 import client, loaded  # noqa: F401 - expose dependent pytest fixture
from app.models import DailyBehavior


CATEGORY_FIELDS = (
    "salty_food",
    "fruit",
    "vegetable",
    "caffeine",
    "smoked",
    "medication",
    "activity_type",
)

NUMERIC_FIELDS = ("sleep_hours", "stress", "activity_minutes")


def test_requested_risk_dimensions_are_exposed_at_daily_grain(loaded):
    data = loaded.get("/api/analytics").json()

    assert data["source_kind"] == "synthetic"
    assert len(data["scatter"]) == data["kpis"]["daily_records"]
    assert data["kpis"]["daily_records"] == len(data["daily_rows"])

    for field in NUMERIC_FIELDS:
        assert all(field in row for row in data["scatter"])

    for field in CATEGORY_FIELDS:
        assert field in data["categories"]


def test_category_counts_exclude_missing_and_match_daily_records(loaded):
    data = loaded.get("/api/analytics").json()

    for field in CATEGORY_FIELDS:
        expected = sum(
            row["sbp_mean"] is not None and row[field] is not None
            for row in data["daily_rows"]
        )
        groups = data["categories"][field]

        assert sum(group["n"] for group in groups) == expected
        assert all(group["n"] > 0 for group in groups)
        assert all(
            0 < group["respondents"] <= data["kpis"]["respondents"]
            for group in groups
        )


def test_numeric_associations_report_pair_and_unique_respondent_counts(loaded):
    data = loaded.get("/api/analytics").json()
    correlations = {row["field"]: row for row in data["correlations"]}

    for field in NUMERIC_FIELDS:
        expected_rows = [
            row for row in data["daily_rows"]
            if row["sbp_mean"] is not None and row[field] is not None
        ]
        result = correlations[field]

        assert result["n"] == len(expected_rows)
        assert result["respondents"] == len(
            {row["respondent_id"] for row in expected_rows}
        )

        if len(expected_rows) < 3 or len(
            {row[field] for row in expected_rows}
        ) < 2:
            assert result["r"] is None


def test_missing_sleep_and_smoking_count_are_not_converted_to_zero(
    loaded, warehouse_engine
):
    data = loaded.get("/api/analytics").json()

    with Session(warehouse_engine) as db:
        missing_sleep = db.scalar(
            select(func.count())
            .select_from(DailyBehavior)
            .where(DailyBehavior.sleep_hours.is_(None))
        )

        missing_smoke_count = db.scalar(
            select(func.count())
            .select_from(DailyBehavior)
            .where(DailyBehavior.smoke_count.is_(None))
        )

    assert data["filtered_quality"]["missing_sleep_hours"] == missing_sleep
    assert data["filtered_quality"]["missing_smoke_count"] == missing_smoke_count

    assert sum(
        row["sleep_hours"] is None for row in data["daily_rows"]
    ) == missing_sleep

    assert sum(
        row["smoke_count"] is None for row in data["daily_rows"]
    ) == missing_smoke_count
