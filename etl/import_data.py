"""CLI for CSV survey import. Run only against a controlled local database.

Usage:
  cd project
  PYTHONPATH=backend SAMPLE_DATA_DIR=data/sample python etl/import_data.py --dry-run
  PYTHONPATH=backend DATABASE_URL=... python etl/import_data.py --profile data/sample/Data_Responden_Sintetis.csv --daily data/sample/Data_Harian_Sintetis.csv --commit --synthetic

--commit replaces *only v2 warehouse* tables and preserves old tables. Always back up a database with real data.
"""
import argparse
import json
import pandas as pd
from app.db import Base, engine, SessionLocal
from app.models import SourceState
from app.pipeline import prepare, load_warehouse

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--profile',default='data/sample/Data_Responden_Sintetis.csv')
    p.add_argument('--daily',default='data/sample/Data_Harian_Sintetis.csv')
    p.add_argument('--synthetic',action='store_true',help='Only for synthetic fixture files')
    p.add_argument('--commit',action='store_true',help='Explicitly replace active v2 warehouse data')
    p.add_argument('--dry-run',action='store_true',help='Validate only (default)')
    args=p.parse_args()
    profiles,days,sessions,quality=prepare(pd.read_csv(args.profile,dtype=str,keep_default_na=False),pd.read_csv(args.daily,dtype=str,keep_default_na=False),synthetic=args.synthetic)
    if args.synthetic and not all(row['respondent_id'].startswith('SIM') for row in profiles):
        raise SystemExit('Flag --synthetic hanya untuk ID SIM...; tolak pelabelan data aktual sebagai sintetis.')
    print(json.dumps(quality,indent=2,ensure_ascii=False))
    if args.commit:
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            load_warehouse(db,profiles,days,sessions,quality,kind='synthetic' if args.synthetic else 'uploaded',source_name='Import ETL manual')
        print('COMMITTED into v2 warehouse. Previous v2 data replaced.')
    else:print('DRY RUN: no database changes. Use --commit to load.')

if __name__=='__main__':main()
