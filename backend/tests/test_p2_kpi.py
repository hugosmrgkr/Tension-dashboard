"""P2-04: definisi KPI, konsistensi dengan filter/periode, dan tidak ada pembanding palsu."""
import pandas as pd
import pytest
from app.analytics_v2 import KPI_DEFINITIONS
from test_cp3_stage1 import client, loaded  # noqa: F401


def get(c, **params):
    r = c.get('/api/analytics', params=params)
    assert r.status_code == 200, r.text
    return r.json()


def valid_sessions(data):
    return [row for row in data['session_rows'] if row['is_valid']]


def test_every_dashboard_kpi_has_written_definition(loaded):
    data = get(loaded)
    assert set(KPI_DEFINITIONS) == {'respondents', 'daily_records', 'sessions', 'mean_sbp'}
    for key, definition in data['kpi_definitions'].items():
        assert key in data['kpis']
        for field in ('label', 'formula', 'unit', 'grain', 'filters', 'source'):
            assert definition[field], (key, field)
    assert 'sebelumnya' in data['comparison_definition']


def test_kpis_match_underlying_rows_and_do_not_double_count_sessions(loaded):
    data = get(loaded)
    k = data['kpis']
    assert k['daily_records'] == len(data['daily_rows'])
    assert k['respondents'] == len({r['respondent_id'] for r in data['daily_rows']})
    assert k['sessions'] == len(valid_sessions(data))
    assert len(data['session_rows']) > k['daily_records']  # dua sesi per hari: catatan harian tidak ikut berlipat
    mean = sum(r['sbp_mean'] for r in valid_sessions(data)) / k['sessions']
    assert k['mean_sbp'] == pytest.approx(round(mean, 1))


@pytest.mark.parametrize('session', ['Pagi', 'Malam'])
def test_session_filter_changes_sessions_but_not_daily_or_respondents(loaded, session):
    base, scoped = get(loaded), get(loaded, session=session)
    rows = [r for r in valid_sessions(base) if r['session'] == session]
    assert scoped['kpis']['sessions'] == len(rows)
    assert scoped['kpis']['mean_sbp'] == pytest.approx(round(sum(r['sbp_mean'] for r in rows) / len(rows), 1))
    assert scoped['kpis']['daily_records'] == base['kpis']['daily_records']
    assert scoped['kpis']['respondents'] == base['kpis']['respondents']


def test_filters_apply_consistently_to_all_kpis(loaded):
    meta = loaded.get('/api/meta').json()
    rid = meta['respondent_ids'][0]
    data = get(loaded, respondent_id=rid)
    assert data['kpis']['respondents'] == 1
    assert {r['respondent_id'] for r in data['session_rows']} == {rid}
    assert data['kpis']['daily_records'] == len(data['daily_rows'])


def test_comparison_equals_independent_query_of_previous_period(loaded):
    meta = loaded.get('/api/meta').json()
    last = pd.Timestamp(meta['max_date'])
    start, end = last - pd.Timedelta(days=9), last  # 10 hari
    data = get(loaded, start_date=str(start.date()), end_date=str(end.date()))
    prev_start, prev_end = start - pd.Timedelta(days=10), start - pd.Timedelta(days=1)
    assert data['comparison']['period'] == f'{prev_start.date()} - {prev_end.date()}'
    previous = get(loaded, start_date=str(prev_start.date()), end_date=str(prev_end.date()))
    assert data['comparison']['has_data'] is True
    assert data['comparison']['active'] == previous['kpis']['respondents']
    assert data['comparison']['daily'] == previous['kpis']['daily_records']
    assert data['comparison']['sessions'] == previous['kpis']['sessions']
    assert data['comparison']['sbp'] == previous['kpis']['mean_sbp']


def test_comparison_respects_non_date_filters(loaded):
    meta = loaded.get('/api/meta').json()
    last = pd.Timestamp(meta['max_date'])
    start, end = last - pd.Timedelta(days=9), last
    pagi = get(loaded, start_date=str(start.date()), end_date=str(end.date()), session='Pagi')
    prev_start, prev_end = start - pd.Timedelta(days=10), start - pd.Timedelta(days=1)
    previous = get(loaded, start_date=str(prev_start.date()), end_date=str(prev_end.date()), session='Pagi')
    assert pagi['comparison']['sessions'] == previous['kpis']['sessions']


def test_no_comparison_without_both_dates_and_no_fake_numbers_when_previous_empty(loaded):
    meta = loaded.get('/api/meta').json()
    assert get(loaded)['comparison'] is None
    assert get(loaded, start_date=meta['min_date'])['comparison'] is None
    assert get(loaded, end_date=meta['max_date'])['comparison'] is None
    first = pd.Timestamp(meta['min_date'])
    data = get(loaded, start_date=str(first.date()), end_date=str((first + pd.Timedelta(days=4)).date()))
    comparison = data['comparison']
    assert comparison['has_data'] is False and comparison['sbp'] is None
    assert comparison['active'] == 0 and comparison['daily'] == 0 and comparison['sessions'] == 0
