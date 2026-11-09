"""Historical API v1 contracts, superseded by CP2/v2/CP3 tests."""
import pytest
pytest.skip('API v1 retired; run the CP2/v2/CP3 serving contracts',allow_module_level=True)
import io
import os
# Import the app with an in-memory URL; fixtures replace its engine/session.
os.environ["DATABASE_URL"] = "sqlite://"

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import main
from app.db import get_db
from app.main import app
from app.data_utils import buat_data_hipertensi_demo

@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", sessions)
    def test_db():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


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


def measurement_values(row):
    return {key: value for key, value in row.items() if key not in ("id", "status_hipertensi")}


def test_edit_keeps_fact_ids_and_reclassifies(client):
    before = client.get("/api/measurements?id_partisipan=P001&page_size=1000").json()["rows"]
    first = before[0]
    values = measurement_values(first)
    values.update(bmi=29.5, sistolik=175)
    result = client.put(f"/api/measurements/{first['id']}", json=values)
    assert result.status_code == 200, result.text
    assert result.json()["id"] == first["id"]
    assert result.json()["status_hipertensi"] == "Hipertensi Tahap 2"
    after = client.get("/api/measurements?id_partisipan=P001&page_size=1000").json()["rows"]
    assert [row["id"] for row in after] == [row["id"] for row in before]
    assert all(row["bmi"] == 29.5 for row in after)
    assert after[1]["sistolik"] == before[1]["sistolik"]


def test_invalid_mutations_leave_dataset_unchanged(client):
    before = client.get("/api/measurements?page_size=2").json()["rows"]
    duplicate = measurement_values(before[0])
    assert client.post("/api/measurements", json=duplicate).status_code == 422
    duplicate["bmi"] = 31.5
    # Moving another measurement onto this same participant/date must fail atomically.
    assert client.put(f"/api/measurements/{before[1]['id']}", json=duplicate).status_code == 422
    after = client.get("/api/measurements?page_size=2").json()["rows"]
    assert after == before
    assert client.get("/api/meta").json()["total_rows"] == 750


def test_reject_inconsistent_participant_on_create(client):
    row = client.get("/api/measurements?page_size=1").json()["rows"][0]
    values = measurement_values(row)
    values.update(tanggal="2025-11-01", bmi=31.5)
    assert client.post("/api/measurements", json=values).status_code == 422
    values["bmi"] = row["bmi"]
    result = client.post("/api/measurements", json=values)
    assert result.status_code == 200, result.text
    assert result.json()["id"] != row["id"]


@pytest.mark.parametrize("filename,content", [
    ("bad.csv", b"x,y\n1,2\n"),
    ("empty.csv", b""),
    ("bad.xlsx", b"not an excel workbook"),
    ("data.txt", b"x,y\n1,2\n"),
])
def test_invalid_upload_preserves_data(client, filename, content):
    before = client.get("/api/analytics").json()
    response = client.post("/api/data/upload", files={"file": (filename, content)})
    assert response.status_code == 422
    assert client.get("/api/analytics").json() == before


def test_upload_excel_and_filtered_exports(client):
    sample = buat_data_hipertensi_demo().iloc[:3]
    workbook = io.BytesIO()
    sample.to_excel(workbook, index=False)
    response = client.post("/api/data/upload", files={"file": ("sample.xlsx", workbook.getvalue())})
    assert response.status_code == 200, response.text
    participant = sample.iloc[0]["id_partisipan"]
    csv = client.get(f"/api/data/export?format=csv&id_partisipan={participant}")
    exported = pd.read_csv(io.BytesIO(csv.content))
    assert exported.id_partisipan.tolist() == [participant]
    assert "id" not in exported.columns
    excel = client.get(f"/api/data/export?format=xlsx&id_partisipan={participant}")
    assert pd.read_excel(io.BytesIO(excel.content)).id_partisipan.tolist() == [participant]
    report = client.get(f"/api/data/export?format=txt&id_partisipan={participant}")
    assert report.status_code == 200
    assert "Total partisipan: 1" in report.text
    assert "sample.xlsx" in report.text


def test_delete_last_measurement_and_reset(client):
    csv = buat_data_hipertensi_demo().iloc[:1].to_csv(index=False).encode()
    assert client.post("/api/data/upload", files={"file": ("one.csv", csv)}).status_code == 200
    row = client.get("/api/measurements").json()["rows"][0]
    assert client.delete(f"/api/measurements/{row['id']}").status_code == 200
    assert client.get("/api/meta").json()["total_rows"] == 0
    assert client.get("/api/analytics").json()["empty"] is True
    assert client.get("/api/measurements").json()["rows"] == []
    for format in ("csv", "xlsx", "txt"):
        assert client.get(f"/api/data/export?format={format}").status_code == 200
    reset = client.post("/api/data/reset")
    assert reset.status_code == 200 and reset.json()["rows"] == 750
    assert client.get("/api/meta").json()["source_kind"] == "demo"


@pytest.mark.parametrize("query", ["page=0", "page_size=0", "page_size=1001", "awal=bad-date"])
def test_invalid_measurement_queries(client, query):
    assert client.get("/api/measurements?" + query).status_code == 422


def test_missing_measurements_and_invalid_export(client):
    values = measurement_values(client.get("/api/measurements?page_size=1").json()["rows"][0])
    assert client.put("/api/measurements/999999", json=values).status_code == 404
    assert client.delete("/api/measurements/999999").status_code == 404
    assert client.get("/api/data/export?format=pdf").status_code == 422


def test_upload_text_lengths_match_database(client):
    sample = buat_data_hipertensi_demo().iloc[:1].copy()
    sample["merokok"] = "x" * 13
    response = client.post("/api/data/upload", files={"file": ("bad.csv", sample.to_csv(index=False).encode())})
    assert response.status_code == 422
    assert client.get("/api/meta").json()["total_rows"] == 750
