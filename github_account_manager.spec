# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Fix for DLL issues
pathex = []
if sys.platform == 'win32':
    # Add common Windows paths to resolve DLL issues
    import os
    pathex.extend([
        os.path.join(os.environ.get('SYSTEMROOT', ''), 'System32'),
        os.path.join(os.environ.get('SYSTEMROOT', ''), 'SysWOW64'),
    ])

# Collect all git-related modules to prevent import errors
git_modules = collect_submodules('git')
request_modules = collect_submodules('requests')

a = Analysis(
    ['github_account_manager.py'],
    pathex=pathex,
    binaries=[],
    datas=[
        # Include git binary if available
    ],
    hiddenimports=[
        # Core modules
        'git', 'git.repo', 'git.repo.base', 'git.remote', 'git.config',
        'git.objects', 'git.objects.blob', 'git.objects.tree', 'git.objects.commit',
        'git.refs', 'git.refs.head', 'git.refs.remote', 'git.refs.tag',
        'git.index', 'git.index.base', 'git.index.typ',
        'git.util', 'git.exc', 'git.cmd',
        # Network modules
        'requests', 'requests.exceptions', 'requests.auth', 'requests.models',
        'urllib3', 'urllib3.util', 'urllib3.util.retry',
        'certifi',
        # GUI modules
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'tkinter.scrolledtext', 'tkinter.simpledialog',
        # Standard library
        'json', 're', 'subprocess', 'platform', 'pathlib', 'os', 'sys',
        'threading', 'queue', 'datetime', 'base64', 'hashlib',
        # Additional modules that might be needed
        'email', 'email.mime', 'email.mime.text',
        'http', 'http.client',
        'ssl', 'socket',
    ] + git_modules + request_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib', 'numpy', 'scipy', 'pandas', 'PIL', 'cv2',
        'tensorflow', 'torch', 'IPython', 'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out problematic binaries on Windows
if sys.platform == 'win32':
    # Remove binaries that might cause DLL conflicts
    a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-win-')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GitHubAccountManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX as it can cause DLL issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
    version='version_info.txt'  # Will create this file
)

# Create app bundle for macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='GitHubAccountManager.app',
        icon=None,
        bundle_identifier='com.example.githubaccountmanager',
        info_plist={
            'CFBundleName': 'GitHubAccountManager',
            'CFBundleDisplayName': 'GitHub Account Manager',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
        }
    )
