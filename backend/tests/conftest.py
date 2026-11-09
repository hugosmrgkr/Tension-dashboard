"""CP2 fixtures use only memory or the explicitly named disposable test database."""
import os
import sys
from pathlib import Path
import pytest
import pandas as pd
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))


@pytest.fixture
def source_pair():
    return tuple(pd.read_csv(ROOT/'data/sample'/name,dtype=str,keep_default_na=False) for name in
                 ['Data_Responden_Sintetis.csv','Data_Harian_Sintetis.csv'])


@pytest.fixture
def prepared(source_pair):
    from app.pipeline import prepare
    return prepare(*source_pair)


@pytest.fixture
def warehouse_engine():
    from app.db import Base
    import app.models
    url=os.getenv('CP2_TEST_DATABASE_URL','sqlite://')
    parsed=make_url(url)
    if parsed.get_backend_name()=='postgresql':
        if parsed.database!='toba_cp2_test' or parsed.host not in ('127.0.0.1','localhost'):
            pytest.fail('CP2_TEST_DATABASE_URL must target disposable localhost/toba_cp2_test, never the active DB')
        engine=create_engine(url)
    elif url=='sqlite://':
        engine=create_engine(url,connect_args={'check_same_thread':False},poolclass=StaticPool)
        @event.listens_for(engine,'connect')
        def enable_foreign_keys(connection,record):
            connection.execute('PRAGMA foreign_keys=ON')
    else:
        pytest.fail('Only in-memory SQLite or the named disposable PostgreSQL database is allowed')
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
