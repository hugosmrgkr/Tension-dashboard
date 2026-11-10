"""Explicit, non-destructive reconciliation of an existing synthetic CP3 warehouse.

Default is read-only dry-run. Commit needs reviewed hash and a pg_dump backup.
Never imports, merges, deletes or replaces a dataset; drift aborts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from backend.app.db import SessionLocal
from backend.app.pipeline import prepare,DataQualityError
from backend.app.baseline import load_experiment
from backend.app.warehouse_sync import reconcile_synthetic

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--commit',action='store_true')
    mode.add_argument('--dry-run',action='store_true')
    parser.add_argument('--expected-current-hash')
    parser.add_argument('--backup-file',help='Existing custom-format pg_dump, never overwritten')
    parser.add_argument('--backup-sha256')
    parser.add_argument('--output',help='JSON evidence path')
    args=parser.parse_args()
    backup_hash=None
    if args.commit:
        if not args.backup_file or not args.backup_sha256 or not args.expected_current_hash:
            parser.error('Commit requires reviewed warehouse hash and backup file/SHA256')
        backup=Path(args.backup_file)
        with backup.open('rb') as handle:
            if handle.read(5)!=b'PGDMP':parser.error('Expected pg_dump custom-format backup')
        with backup.open('rb') as handle:backup_hash=hashlib.file_digest(handle,'sha256').hexdigest()
        if backup_hash!=args.backup_sha256:parser.error('Backup SHA256 does not match')
    prepared=prepare(*[pd.read_csv(ROOT/'data/sample'/name,dtype=str,keep_default_na=False)
                      for name in ['Data_Responden_Sintetis.csv','Data_Harian_Sintetis.csv']])
    artifact=load_experiment(ROOT/'models')
    if not artifact['available'] or artifact['provenance']['prepared_content_sha256']!=prepared[3]['prepared_content_sha256']:
        raise DataQualityError('Verified baseline and fixture fingerprints must match before synchronization')
    with SessionLocal() as db:
        if not args.commit and db.bind.dialect.name=='postgresql':db.execute(text('SET TRANSACTION READ ONLY'))
        result=reconcile_synthetic(db,prepared,commit=args.commit,expected_current_hash=args.expected_current_hash)
    result.update(artifact_run_id=artifact['run_id'],backup_sha256=backup_hash)
    serialized=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(serialized,encoding='utf-8')
    print(serialized)


if __name__=='__main__':main()
