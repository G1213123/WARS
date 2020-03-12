# -*- mode: python ; coding: utf-8 -*-

import sys

sys.setrecursionlimit(5000)

block_cipher = None


a = Analysis(['gui_master.py'],
             pathex=['C:\\Users\\ngwin\\Documents\\Python_Scripts\\WARS'],
             binaries=[],
             datas=[("C:\\Users\\ngwin\\pyinstall-env\\Lib\\site-packages\\branca\\*.json","branca"),
			 ("C:\\Users\\ngwin\\pyinstall-env\\Lib\\site-packages\\branca\\templates\\color_scale.js","."),
			 ("C:\\Users\\ngwin\\pyinstall-env\\Lib\\site-packages\\folium\\templates","templates"),],
             hiddenimports=[],
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
		  a.binaries,
		  a.zipfiles,
		  a.datas,
          [],
          exclude_binaries=True,
          name='gui_master',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='gui_master')
