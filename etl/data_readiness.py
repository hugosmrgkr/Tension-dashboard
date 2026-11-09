"""Build the CP2 simulation reports and EDA figures without touching a database.

Run from project root: python -m etl.data_readiness --synthetic
"""
import argparse
import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path
import pandas as pd
from backend.app.pipeline import prepare
from backend.app.readiness import analyze, make_figures, dictionary_markdown, quality_markdown, findings_markdown


def write_quality_files(quality, target):
    target=Path(target); target.mkdir(parents=True,exist_ok=True)
    (target/'quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for phase in ('before','after'):
        pd.DataFrame(quality[phase]).to_csv(target/f'completeness_{phase}.csv',index=False,encoding='utf-8-sig')
    issues=quality['issues'] + [dict(source='profiles',code='quarantined_row',**r) for r in quality['profile_rejections']] + [
        dict(source='daily',code='quarantined_row',**r) for r in quality['rejections']]
    pd.DataFrame(issues,columns=['source','row','column','field','code','action','reason']).to_csv(target/'issues.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(quality['pressure_anomalies']['flags'],columns=['session_index','source_row','session','field','value','action','method']).to_csv(target/'pressure_anomalies.csv',index=False,encoding='utf-8-sig')


def generate(root):
    root=Path(root).resolve()
    paths=[root/'data/sample/Data_Responden_Sintetis.csv',root/'data/sample/Data_Harian_Sintetis.csv']
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    raw=[pd.read_csv(p,dtype=str,keep_default_na=False) for p in paths]
    p,d,s,q=prepare(*raw,synthetic=True)
    if not all(row['respondent_id'].startswith('SIM') for row in p):
        raise ValueError('Laporan publik ini hanya untuk fixture SIM, bukan data aktual')
    report=root/'reports/cp2'; docs=root/'docs'
    report.mkdir(parents=True,exist_ok=True); docs.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(root/'reports/.matplotlib'))
    os.environ.setdefault('MPLBACKEND','Agg')
    write_quality_files(q,report)
    manifest=dict(label='SIMULASI',source_sha256=hashes,source_shapes={paths[i].name:list(df.shape) for i,df in enumerate(raw)},
                  pipeline_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'backend/app/pipeline.py',root/'backend/app/survey_schema.py',root/'backend/app/quality.py',root/'backend/app/readiness.py']},
                  rows=q['row_outcomes'],python=sys.version,
                  environment={name:version(name) for name in ['pandas','numpy','sqlalchemy','matplotlib','nbformat','nbclient','psycopg']})
    (report/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    eda=analyze(p,d,s,q)
    (report/'eda_summary.json').write_text(json.dumps(eda['summary'],ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    numeric={'profiles':eda['profiles'][['age','height_cm','weight_kg','bmi','active_days_week']],
             'sessions':eda['valid_sessions'][['sbp_mean','dbp_mean']],
             'daily':eda['daily'][['sleep_hours','activity_minutes','heavy_minutes','stress','sbp_mean','dbp_mean']]}
    for name,df in numeric.items():
        df.describe().to_csv(report/f'descriptive_{name}.csv',encoding='utf-8-sig')
    eda['correlation'].to_csv(report/'correlation_daily.csv',encoding='utf-8-sig')
    figs=make_figures(eda,q); figure_dir=report/'figures'; figure_dir.mkdir(exist_ok=True)
    import matplotlib.pyplot as plt
    for name,fig in figs.items():
        fig.savefig(figure_dir/name,dpi=120,bbox_inches='tight'); plt.close(fig)
    (docs/'DATA_DICTIONARY.md').write_text(dictionary_markdown(),encoding='utf-8')
    (docs/'DATA_QUALITY_REPORT.md').write_text(quality_markdown(q,manifest),encoding='utf-8')
    (docs/'EDA_FINDINGS.md').write_text(findings_markdown(eda),encoding='utf-8')
    assert hashes=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, 'Raw sources changed'
    return q,eda['summary']


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic',action='store_true',required=True,help='Acknowledge reports are simulation only')
    args=parser.parse_args()
    q,summary=generate(Path(__file__).resolve().parents[1])
    print(json.dumps(dict(label='SIMULASI',rows=q['row_outcomes'],findings=summary['findings']),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
