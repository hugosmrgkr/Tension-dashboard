"""Exercise the real ZIP script on a fake project, never on repository data."""
import subprocess
import sys
import zipfile
from pathlib import Path


def test_archive_excludes_private_backups_credentials_and_keeps_public_sources(tmp_path):
    root=tmp_path/'source';root.mkdir()
    script=Path(__file__).resolve().parents[2]/'buat_zip.py'
    (root/'buat_zip.py').write_bytes(script.read_bytes())
    excluded=['data/private/backups/main.dump','data/actual/person.csv','data/raw/form.xlsx',
              'credentials.json','credentials-prod.json','service-account-prod.json','private.key',
              'cert.PEM','main.dump','local.db','.env','backend/.env.local','.aws/credentials']
    included=['README.md','.env.example','data/sample/example.csv','frontend/package-lock.json']
    for name in excluded+included:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('test fixture',encoding='utf-8')
    subprocess.run([sys.executable,str(root/'buat_zip.py')],check=True,capture_output=True)
    with zipfile.ZipFile(tmp_path/'mental-health-dashboard-source.zip') as archive:
        names=set(archive.namelist())
    assert all('source/'+name not in names for name in excluded)
    assert all('source/'+name in names for name in included)
