"""Read-only equivalence of CP2 warehouse windows and offline baseline artifacts."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text
from backend.app.db import SessionLocal
from backend.app.analytics_v2 import frames
from backend.app.baseline import make_training,FEATURES,load_experiment


def main():
    with SessionLocal() as db:
        if db.bind.dialect.name=='postgresql':db.execute(text('SET TRANSACTION READ ONLY'))
        profiles,sessions,days=frames(db)
        windows=make_training(profiles.to_dict('records'),days.to_dict('records'),sessions.to_dict('records'))
    expected=pd.read_csv('reports/cp3_baseline/all_windows.csv')
    pd.testing.assert_frame_equal(windows.reset_index(drop=True),expected,check_dtype=False,atol=1e-10,rtol=1e-10)
    metrics=load_experiment('models');assert metrics['available']
    selected=windows.merge(pd.DataFrame(metrics['actual_vs_predicted'])[['respondent_id','date']].rename(columns={'date':'asof_date'}),on=['respondent_id','asof_date'],validate='one_to_one')
    predicted=joblib.load('models/linear_regression_synthetic.joblib').predict(selected[FEATURES])
    stored=pd.DataFrame(metrics['actual_vs_predicted']).linear.to_numpy()
    np.testing.assert_allclose(predicted,stored,atol=1e-9,rtol=1e-9)
    print(json.dumps(dict(warehouse_windows_equal_offline_csv=True,windows=len(windows),primary_test_rows=len(selected),
        warehouse_linear_predictions_equal_artifact=True,max_abs_prediction_difference=float(np.max(np.abs(predicted-stored))),model_run_id=metrics['run_id']),indent=2))

if __name__=='__main__':main()
