# PyInstaller spec for Job Search Agent.
#
# Build on a WINDOWS machine (PyInstaller does not cross-compile) with:
#     pyinstaller job_agent.spec
#
# Or just run BUILD_INSTALLER.bat, which does this step for you along
# with everything else. Output: dist\JobSearchAgent.exe

block_cipher = None

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'werkzeug',
        'werkzeug.serving',
        'flask',
        'playwright',
        'playwright.sync_api',
        'feedparser',
        'docx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JobSearchAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # keep the status window visible (progress, errors)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # set to e.g. 'icon.ico' if you add one
)
