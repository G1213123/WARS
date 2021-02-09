# -*- mode: python ; coding: utf-8 -*-
# for branca/jinja2 issue see https://github.com/pyinstaller/pyinstaller/issues/5256

import sys

sys.setrecursionlimit(5000)

block_cipher = None

import os

env_path = os.environ['CONDA_PREFIX']
dlls = os.path.join(env_path, 'DLLs')
bins = os.path.join(env_path, 'Library', 'bin')

binaries = [
    (os.path.join(bins,'geos.dll'), '.'),
    (os.path.join(bins,'geos_c.dll'), '.'),
    (os.path.join(bins,'spatialindex_c-64.dll'), '.'),
    (os.path.join(bins,'spatialindex-64.dll'),'.'),
]

a = Analysis(['C:\\Users\\Andrew.WF.Ng\\Documents\\Python_Scripts\\WARS\\gui_master.py'],
             pathex=['C:\\Users\\Andrew.WF.Ng\\Documents\\exe'],
             datas=[("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\branca\\*.json","branca"),
			 ("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\branca\\templates\\color_scale.js","templates"),
			 ("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\folium\\templates","templates"),],
             hiddenimports=['fiona._shim','fiona.schema','pyproj._datadir','pyproj.datadir'],
			 binaries=binaries,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='gui_master',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='gui_master')
