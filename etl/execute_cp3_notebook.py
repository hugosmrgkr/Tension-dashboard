"""Execute CP3 notebook using the invoking Python, without installing a global kernel."""
import json
import os
import sys
import tempfile
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    root=Path(__file__).resolve().parents[1]
    os.environ.setdefault('MPLCONFIGDIR',str(root/'reports/.matplotlib'))
    os.environ.setdefault('IPYTHONDIR',str(root/'reports/.jupyter/ipython'))
    os.environ.setdefault('JUPYTER_RUNTIME_DIR',str(root/'reports/.jupyter/runtime'))
    for variable in ('IPYTHONDIR','JUPYTER_RUNTIME_DIR'):
        Path(os.environ[variable]).mkdir(parents=True,exist_ok=True)
    notebook=root/'notebooks/03_verifikasi_baseline_cp3.ipynb'
    nb=nbformat.read(notebook,as_version=4)
    with tempfile.TemporaryDirectory(prefix='toba_cp3_kernel_') as folder:
        spec=Path(folder)/'cp3'; spec.mkdir()
        (spec/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                                      display_name='Toba CP3 isolated',language='python')),encoding='utf-8')
        manager=KernelSpecManager(kernel_dirs=[folder])
        km=KernelManager(kernel_name='cp3',kernel_spec_manager=manager)
        client=NotebookClient(nb,km=km,timeout=180,resources={'metadata':{'path':str(root)}},record_timing=False)
        try:
            client.execute()
        finally:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
    nbformat.write(nb,notebook)
    count=sum(c.cell_type=='code' for c in nb.cells)
    print(f'Executed {count} code cells successfully: {notebook.name}')


if __name__=='__main__':
    main()
