"""Git index checkout simulation, without committing or changing the real index."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=r'''
import json,os
from pathlib import Path
os.environ['DATABASE_URL']='sqlite://'
os.environ['MODEL_DIR']=str(Path.cwd()/'models')
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app import main
from app.db import Base,get_db
from app.pipeline import prepare,load_warehouse
from app.baseline import load_experiment
import pandas as pd
engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
main.engine=engine;Base.metadata.create_all(engine)
p,d,s,q=prepare(pd.read_csv('data/sample/Data_Responden_Sintetis.csv',dtype=str,keep_default_na=False),pd.read_csv('data/sample/Data_Harian_Sintetis.csv',dtype=str,keep_default_na=False))
with Session(engine) as db:load_warehouse(db,p,d,s,q)
def database():
    with Session(engine) as db:yield db
main.app.dependency_overrides[get_db]=database
with TestClient(main.app) as client:
    result=client.get('/api/model/baseline');prediction=client.get('/api/model/predict-baseline?respondent_id=SIM001')
    assert result.status_code==prediction.status_code==200 and result.json()['available']
    assert result.json()['warehouse_batch_match']
print(json.dumps(dict(available=True,prediction_status=prediction.status_code,run_id=result.json()['run_id'],metrics_crlf=Path('models/baseline_metrics.json').read_bytes().count(b'\r\n'))))
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='reports/p0_p1_audit/checkout-windows.json');args=parser.parse_args()
    results=[]
    with tempfile.TemporaryDirectory(prefix='toba-audit-checkout-') as scratch:
        base=Path(scratch);repo=base/'index-source';repo.mkdir()
        shutil.copyfile(ROOT/'.gitattributes',repo/'.gitattributes')
        for folder in ['backend/app','models','data/sample']:
            for source in (ROOT/folder).rglob('*'):
                if not source.is_file() or '__pycache__' in source.parts:continue
                target=repo/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        def git(*args):
            return subprocess.run(['git',*args],cwd=repo,check=True,capture_output=True,text=True)
        git('init','-q');git('config','core.autocrlf','false');git('add','.')
        for autocrlf in ['false','true']:
            target=base/('linux-style' if autocrlf=='false' else 'windows-style');target.mkdir()
            git('-c','core.autocrlf='+autocrlf,'checkout-index','--all','--prefix',str(target).replace('\\','/')+'/')
            env={**os.environ,'PYTHONPATH':str(target/'backend'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
            result=subprocess.run([sys.executable,'-c',PROBE],cwd=target,env=env,check=True,capture_output=True,text=True)
            evidence=json.loads(result.stdout.splitlines()[-1]);evidence['git_core_autocrlf']=autocrlf
            evidence['binary_sha256_unchanged']=hashlib.sha256((target/'models/linear_regression_synthetic.joblib').read_bytes()).digest()==hashlib.sha256((ROOT/'models/linear_regression_synthetic.joblib').read_bytes()).digest()
            assert evidence['binary_sha256_unchanged'];results.append(evidence)
    output=ROOT/args.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(dict(platform=sys.platform,git_checkout_index=True,real_repository_index_modified=False,results=results),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
