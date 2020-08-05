# -*- mode: python ; coding: utf-8 -*-

import sys

sys.setrecursionlimit(5000)

block_cipher = None



a = Analysis(['C:\\Users\\Andrew.WF.Ng\\Documents\\Python_Scripts\\WARS\\gui_master.py'],
             pathex=['C:\\Users\\Andrew.WF.Ng\\Documents\\exe'],
             datas=[("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\branca\\*.json","branca"),
			 ("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\branca\\templates\\color_scale.js","templates"),
			 ("C:\\Users\\Andrew.WF.Ng\\AppData\\Local\\Continuum\\anaconda3\\Lib\\site-packages\\folium\\templates","templates"),],
             hiddenimports=['fiona._shim','fiona.schma'],
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
