"""P2-07: nama tampilan konsisten dan nama operasional yang berisiko tidak berubah."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = 'Toba Health Insight'
read = lambda rel: (ROOT / rel).read_text(encoding='utf-8')


def test_display_name_is_consistent_in_every_user_facing_place():
    assert '<title>' + NAME + '</title>' in read('frontend/index.html')
    assert read('README.md').splitlines()[0].startswith('# ' + NAME)
    assert "title='" + NAME + " API'" in read('backend/app/main.py')
    common = read('frontend/src/components/Common.jsx')
    assert common.count(NAME) >= 2  # sidebar dan footer
    assert read('backend/app/__init__.py').startswith('"""' + NAME)


def test_old_name_does_not_appear_in_user_facing_source():
    pattern = re.compile(r'mental[-_ ]health', re.I)
    for rel in ['frontend/index.html', 'README.md', 'backend/app/main.py', 'backend/app/analytics_v2.py']:
        assert not pattern.search(read(rel)), rel
    for path in (ROOT / 'frontend/src/components').glob('*.jsx'):
        assert not pattern.search(path.read_text(encoding='utf-8')), path.name
    for path in (ROOT / 'frontend/src/pages').glob('Pages.jsx'):
        assert not pattern.search(path.read_text(encoding='utf-8')), path.name


def test_operational_names_stay_stable_to_protect_existing_volumes():
    start = read('scripts/start_main.ps1')
    assert '-p tension-dashboard' in start
    for compose in ('compose.yaml', 'compose.prod.yaml'):
        text = read(compose)
        assert 'POSTGRES_DB: toba_health' in text and 'POSTGRES_USER: toba' in text
    assert 'postgres_data:' in read('compose.yaml')


def test_branding_doc_lists_pending_items():
    doc = read('docs/BRANDING.md')
    assert 'buat_zip.py' in doc and 'tension-dashboard' in doc and 'menunggu konfirmasi' in doc
