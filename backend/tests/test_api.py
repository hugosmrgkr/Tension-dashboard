"""API smoke/integration tests. Run from backend dir: pytest -q."""
import io
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(__file__).parent / "test_toba.db")

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.data_utils import buat_data_hipertensi_demo

@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post("/api/data/reset")
        yield c


def test_seed_matches_generator(client):
    meta = client.get("/api/meta").json()
    assert meta["total_rows"] == 750
    assert meta["source_kind"] == "demo"
    a = client.get("/api/analytics").json()
    assert a["total_participants"] == 25
    assert a["distribution"][0]["count"] == 17
    assert a["distribution"][1]["count"] == 5
    assert a["distribution"][2]["count"] == 3
    assert a["non_normal"] == 8
    assert a["non_normal_percent"] == 32
    assert a["days"] == 30


def test_global_filter_and_pagination(client):
    result = client.get("/api/measurements?page=1&page_size=7").json()
    assert result["total"] == 750 and len(result["rows"]) == 7
    r = client.get("/api/analytics?awal=2025-10-01&akhir=2025-10-05").json()
    assert r["days"] == 5 and r["total_rows"] == 125
    r = client.get("/api/analytics?id_partisipan=P001").json()
    assert r["total_participants"] == 1 and r["total_rows"] == 30


def test_prediction_is_demo_not_ml(client):
    r = client.post("/api/predict/demo", json={"usia":35,"bmi":24,"sistolik":145,"diastolik":91})
    assert r.status_code == 200
    assert r.json()["status"] == "Hipertensi Tahap 1"
    assert r.json()["is_ml"] is False
    assert client.get("/api/model/demo").json()["is_placeholder"] is True


def test_upload_validation_and_csv_export(client):
    demo = buat_data_hipertensi_demo().iloc[:8].copy()
    csv = demo.to_csv(index=False).encode("utf-8")
    r = client.post("/api/data/upload", files={"file": ("demo_subset.csv", io.BytesIO(csv),"text/csv")})
    assert r.status_code == 200, r.text
    assert client.get("/api/meta").json()["total_rows"] == 8
    out = client.get("/api/data/export?format=csv")
    assert out.status_code == 200
    assert len(pd.read_csv(io.BytesIO(out.content))) == 8
    wrong = client.post("/api/data/upload", files={"file":("bad.csv", b"x,y\n1,2\n", "text/csv")})
    assert wrong.status_code == 422
    assert client.get("/api/meta").json()["total_rows"] == 8


def test_edit_and_delete(client):
    row = client.get("/api/measurements?page_size=1").json()["rows"][0]
    old_id = row["id"]
    patch = {key:value for key,value in row.items() if key not in ("id","status_hipertensi")}
    patch["sistolik"] = 170
    patch["bmi"] = 28.5
    resp = client.put(f"/api/measurements/{old_id}", json=patch)
    assert resp.status_code==200,resp.text
    filtered = client.get("/api/measurements?id_partisipan="+row["id_partisipan"]+"&page_size=40").json()["rows"]
    assert len(filtered)==30
    assert all(r["bmi"]==28.5 for r in filtered)
    edited = [r for r in filtered if r["tanggal"]==row["tanggal"]][0]
    assert edited["status_hipertensi"]=="Hipertensi Tahap 2"
    deleted=client.delete("/api/measurements/"+str(edited["id"]))
    assert deleted.status_code == 200
    assert client.get("/api/meta").json()["total_rows"] == 749


def test_create_record_and_excel(client):
    sample=client.get("/api/measurements?page_size=1").json()["rows"][0]
    record={key:value for key,value in sample.items() if key not in ('id','status_hipertensi')}
    record['id_partisipan']='NEW99'
    record['tanggal']='2025-11-01'
    r=client.post('/api/measurements',json=record)
    assert r.status_code==200,r.text
    excel=client.get('/api/data/export?format=xlsx')
    assert excel.status_code==200 and excel.content.startswith(b'PK')
