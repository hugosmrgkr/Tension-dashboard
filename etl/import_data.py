"""Import CSV/XLSX into PostgreSQL/SQLite as one repeatable ETL batch.
Run from repository root: python -m etl.import_data data/your_file.csv
"""
import argparse
from pathlib import Path
import pandas as pd
from backend.app.db import Base, engine, SessionLocal
from backend.app.service import replace_data

parser = argparse.ArgumentParser(description="Toba Health Insight ETL")
parser.add_argument("file", help="Path to CSV or XLSX")
args = parser.parse_args()
source=Path(args.file)
if not source.is_file() or source.suffix.lower() not in {'.csv','.xlsx'}:
    parser.error('Pilih file CSV atau XLSX yang valid')
df=(pd.read_csv(source,encoding='utf-8-sig') if source.suffix.lower()=='.csv' else pd.read_excel(source))
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    count=replace_data(db,df,source.name,'uploaded')
print(f'Berhasil impor {count} pengukuran dari {source}')
