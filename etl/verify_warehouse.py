"""Read-only warehouse inspection. Never creates, seeds, resets or changes tables."""
import json
import argparse
from pathlib import Path
from sqlalchemy import text
from backend.app.db import SessionLocal
from backend.app.warehouse_audit import audit_warehouse


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='Optional JSON report path; database remains read-only')
    args=parser.parse_args()
    with SessionLocal() as db:
        if db.bind.dialect.name=='postgresql':
            db.execute(text('SET TRANSACTION READ ONLY'))
        result=audit_warehouse(db)
        if args.output:
            target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
