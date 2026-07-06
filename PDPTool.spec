# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('training_plans', 'training_plans'), ('files', 'files'), ('coding_problems', 'coding_problems'), ('_pdf_preview', '_pdf_preview'), ('人才培养', '人才培养'), ('pdptool.db', '.'), ('pdptool_config.json', '.')],
    hiddenimports=['matplotlib.backends.backend_qtagg', 'markdown'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'sklearn', 'scipy', 'bokeh', 'selenium', 'transformers', 'datasets', 'PyQt5', 'sphinx', 'nbformat', 'black', 'jedi', 'IPython', 'jupyter', 'notebook', 'zmq', 'tornado', 'babel', 'docutils', 'yapf', 'PIL', 'cv2', 'plotly', 'dask', 'xarray', 'statsmodels', 'sqlalchemy', 'numexpr', 'numba', 'h5py', 'pytz'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDPTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDPTool',
)
