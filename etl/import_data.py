"""CLI for CSV survey import. Run only against a controlled local database.

Usage:
  cd project
  python -m etl.import_data --synthetic --dry-run
  PYTHONPATH=backend DATABASE_URL=... python etl/import_data.py --profile data/sample/Data_Responden_Sintetis.csv --daily data/sample/Data_Harian_Sintetis.csv --commit --synthetic

--commit replaces *only v2 warehouse* tables and preserves old tables. Always back up a database with real data.
"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.db import Base, engine, SessionLocal
from backend.app.pipeline import prepare, DataQualityError
from backend.app.etl_control import apply_validated

def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser()
    p.add_argument('--profile',default='data/sample/Data_Responden_Sintetis.csv')
    p.add_argument('--daily',default='data/sample/Data_Harian_Sintetis.csv')
    p.add_argument('--synthetic',action='store_true',help='Only for synthetic fixture files')
    p.add_argument('--source-kind',choices=['synthetic','actual'],help='Source classification; --synthetic is a compatibility alias')
    p.add_argument('--expected-current-hash',help='Required precondition for an occupied warehouse; obtain with verify_warehouse')
    p.add_argument('--allow-source-change',action='store_true',help='Explicitly acknowledge changing source kind; never merges sources')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--commit',action='store_true',help='Explicitly replace active v2 warehouse data')
    mode.add_argument('--dry-run',action='store_true',help='Validate only (default)')
    p.add_argument('--report-dir',help='Write structured quality reports; sources remain untouched')
    p.add_argument('--summary',action='store_true',help='Print row outcomes instead of the full per-column audit')
    args=p.parse_args()
    if args.synthetic and args.source_kind=='actual':
        p.error('--synthetic tidak dapat digabung dengan --source-kind actual')
    kind=args.source_kind or ('synthetic' if args.synthetic else 'actual')
    sample=Path(__file__).resolve().parents[1]/'data/sample'
    if kind=='actual' and any(Path(path).resolve().is_relative_to(sample.resolve()) for path in (args.profile,args.daily)):
        p.error('File data/sample adalah fixture sintetis. Gunakan --synthetic; data aktual harus terpisah.')
    if kind=='actual' and args.report_dir and not Path(args.report_dir).resolve().is_relative_to((sample.parent/'private').resolve()):
        p.error('Laporan aktual harus disimpan pada data/private/ yang diabaikan Git, bukan reports publik.')
    try:
        profiles,days,sessions,quality=prepare(pd.read_csv(args.profile,dtype=str,keep_default_na=False),pd.read_csv(args.daily,dtype=str,keep_default_na=False),synthetic=kind=='synthetic')
    except DataQualityError as exc:
        if args.report_dir:
            from etl.data_readiness import write_quality_files
            target=Path(args.report_dir);target.mkdir(parents=True,exist_ok=True)
            if hasattr(exc,'quality'):
                write_quality_files(exc.quality,target)
            (target/'batch_error.json').write_text(json.dumps(dict(status='batch_rejected',reason=str(exc),database_changed=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        p.exit(2,'ETL batch rejected; database unchanged: '+str(exc)+'\n')
    if kind=='synthetic' and not all(row['respondent_id'].startswith('SIM') for row in profiles):
        raise SystemExit('Flag --synthetic hanya untuk ID SIM...; tolak pelabelan data aktual sebagai sintetis.')
    quality['source_kind']=kind
    print(json.dumps(quality['row_outcomes'] if args.summary else quality,indent=2,ensure_ascii=False))
    if args.report_dir:
        from etl.data_readiness import write_quality_files
        write_quality_files(quality,args.report_dir)
    if args.commit:
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            try:
                result=apply_validated(db,profiles,days,sessions,quality,kind=kind,
                                       expected_current_hash=args.expected_current_hash,allow_source_change=args.allow_source_change)
            except DataQualityError as exc:
                db.rollback();p.exit(2,str(exc)+'\n')
        print('COMMITTED explicit ETL; natural content SHA-256: '+result['natural_content_sha256'])
    else:print('DRY RUN: no database changes. Use --commit to load.')

if __name__=='__main__':main()
