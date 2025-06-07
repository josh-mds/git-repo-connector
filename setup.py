#!/usr/bin/env python3
"""
Advanced Setup script for GitHub Account Manager
Fixes DLL issues and creates proper cross-platform installers
"""

import os
import sys
import subprocess
import shutil
import platform
import json
from pathlib import Path

class GitHubAccountManagerBuilder:
    def __init__(self):
        self.platform = platform.system()
        self.arch = platform.machine()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.project_name = "GitHubAccountManager"
        
    def install_dependencies(self):
        """Install required dependencies with error handling"""
        dependencies = [
            'GitPython>=3.1.0',
            'requests>=2.25.0',
            'pyinstaller>=5.0.0',
            'setuptools>=45.0.0',
            'wheel>=0.36.0'
        ]
        
        print("Installing dependencies...")
        failed_deps = []
        
        for dep in dependencies:
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--upgrade', dep
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✓ Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {dep}")
                failed_deps.append(dep)
        
        if failed_deps:
            print(f"❌ Failed to install: {', '.join(failed_deps)}")
            return False
        return True

    def create_fixed_spec_file(self):
        """Create PyInstaller spec file with DLL fixes"""
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

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
    hooksconfig={{}},
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
    name='{self.project_name}',
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
        name='{self.project_name}.app',
        icon=None,
        bundle_identifier='com.example.githubaccountmanager',
        info_plist={{
            'CFBundleName': '{self.project_name}',
            'CFBundleDisplayName': 'GitHub Account Manager',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
        }}
    )
"""
        
        with open('github_account_manager.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print("✓ Created fixed spec file")

    def create_version_info(self):
        """Create version info file for Windows executable"""
        if self.platform != 'Windows':
            return
            
        version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'GitHub Account Manager'),
        StringStruct(u'FileDescription', u'GitHub Account Manager'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'GitHubAccountManager'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'GitHubAccountManager.exe'),
        StringStruct(u'ProductName', u'GitHub Account Manager'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
        
        with open('version_info.txt', 'w', encoding='utf-8') as f:
            f.write(version_info)
        print("✓ Created version info file")

    def build_executable(self):
        """Build executable with enhanced error handling"""
        print(f"\n=== Building {self.platform} Executable ===")
        
        try:
            # Clean previous builds
            if os.path.exists('dist'):
                shutil.rmtree('dist')
            if os.path.exists('build'):
                shutil.rmtree('build')
            
            # Build using spec file
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                'github_account_manager.spec'
            ]
            
            print("Building executable... (this may take a few minutes)")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Build failed!")
                print("STDERR:", result.stderr)
                return False
            
            # Check if build was successful
            exe_name = f"{self.project_name}.exe" if self.platform == 'Windows' else self.project_name
            exe_path = Path('dist') / exe_name
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024*1024)
                print(f"✓ Successfully created executable: {exe_path.absolute()}")
                print(f"  File size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Executable not found in dist/ folder")
                print("Available files:", list(Path('dist').glob('*')) if Path('dist').exists() else "None")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def create_universal_installer(self):
        """Create a cross-platform installer script"""
        print("\n=== Creating Universal Installer ===")
        
        # Create installer data
        installer_data = {
            "name": "GitHub Account Manager",
            "version": "1.0.0",
            "description": "Manage multiple GitHub accounts and repositories",
            "author": "GitHub Account Manager Team",
            "platforms": {
                "windows": {
                    "executable": "GitHubAccountManager.exe",
                    "requirements": ["Git for Windows"],
                    "install_path": "%APPDATA%\\GitHubAccountManager"
                },
                "darwin": {
                    "executable": "GitHubAccountManager.app",
                    "requirements": ["Git", "Xcode Command Line Tools"],
                    "install_path": "/Applications"
                },
                "linux": {
                    "executable": "GitHubAccountManager",
                    "requirements": ["git", "python3-tk"],
                    "install_path": "/opt/githubaccountmanager"
                }
            }
        }
        
        with open('installer_data.json', 'w', encoding='utf-8') as f:
            json.dump(installer_data, f, indent=2)
        
        # Create cross-platform installer script
        installer_script = '''#!/usr/bin/env python3
"""
Universal installer for GitHub Account Manager
Auto-detects platform and installs accordingly
"""

import sys
import os
import platform
import subprocess
import shutil
import json
from pathlib import Path

class UniversalInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_admin = self.check_admin_privileges()
        
        # Load installer data
        with open('installer_data.json', 'r') as f:
            self.config = json.load(f)
    
    def check_admin_privileges(self):
        """Check if running with admin privileges"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def install_windows(self):
        """Install on Windows"""
        print("Installing GitHub Account Manager for Windows...")
        
        # Check for Git
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            print("✓ Git is installed")
        except:
            print("❌ Git not found. Please install Git for Windows first.")
            print("   Download from: https://git-scm.com/download/win")
            return False
        
        # Create install directory
        install_path = Path(os.path.expandvars(self.config['platforms']['windows']['install_path']))
        install_path.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        exe_path = Path('dist') / self.config['platforms']['windows']['executable']
        if exe_path.exists():
            shutil.copy2(exe_path, install_path)
            print(f"✓ Installed to {install_path}")
            
            # Create desktop shortcut
            self.create_windows_shortcut(install_path / self.config['platforms']['windows']['executable'])
            return True
        else:
            print(f"❌ Executable not found: {exe_path}")
            return False
    
    def install_macos(self):
        """Install on macOS"""
        print("Installing GitHub Account Manager for macOS...")
        
        # Check for dependencies
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            print("✓ Git is installed")
        except:
            print("❌ Git not found. Please install Xcode Command Line Tools:")
            print("   Run: xcode-select --install")
            return False
        
        # Install app bundle
        app_path = Path('dist') / self.config['platforms']['darwin']['executable']
        install_path = Path(self.config['platforms']['darwin']['install_path'])
        
        if app_path.exists():
            if install_path.exists():
                shutil.rmtree(install_path / app_path.name)
            shutil.copytree(app_path, install_path / app_path.name)
            print(f"✓ Installed to {install_path / app_path.name}")
            return True
        else:
            print(f"❌ App bundle not found: {app_path}")
            return False
    
    def install_linux(self):
        """Install on Linux"""
        print("Installing GitHub Account Manager for Linux...")
        
        # Check for dependencies
        missing_deps = []
        
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            print("✓ Git is installed")
        except:
            missing_deps.append('git')
        
        # Check for tkinter
        try:
            import tkinter
            print("✓ tkinter is available")
        except ImportError:
            missing_deps.append('python3-tk')
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("Install with your package manager, e.g.:")
            print(f"   sudo apt install {' '.join(missing_deps)}")
            return False
        
        # Install executable
        exe_path = Path('dist') / self.config['platforms']['linux']['executable']
        install_path = Path(self.config['platforms']['linux']['install_path'])
        
        if exe_path.exists():
            install_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe_path, install_path)
            os.chmod(install_path / exe_path.name, 0o755)
            
            # Create desktop entry
            self.create_linux_desktop_entry(install_path / exe_path.name)
            print(f"✓ Installed to {install_path}")
            return True
        else:
            print(f"❌ Executable not found: {exe_path}")
            return False
    
    def create_windows_shortcut(self, exe_path):
        """Create Windows desktop shortcut"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "GitHub Account Manager.lnk")
            target = str(exe_path)
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = str(exe_path.parent)
            shortcut.IconLocation = target
            shortcut.save()
            print("✓ Created desktop shortcut")
        except ImportError:
            print("⚠️  Could not create desktop shortcut (pywin32 not installed)")
        except Exception as e:
            print(f"⚠️  Could not create desktop shortcut: {e}")
    
    def create_linux_desktop_entry(self, exe_path):
        """Create Linux desktop entry"""
        desktop_entry = f"""[Desktop Entry]
Name=GitHub Account Manager
Comment=Manage multiple GitHub accounts and repositories
Exec={exe_path}
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;VersionControl;
"""
        
        desktop_path = Path.home() / 'Desktop' / 'github-account-manager.desktop'
        try:
            with open(desktop_path, 'w') as f:
                f.write(desktop_entry)
            os.chmod(desktop_path, 0o755)
            print("✓ Created desktop entry")
        except Exception as e:
            print(f"⚠️  Could not create desktop entry: {e}")
    
    def run(self):
        """Run the installer"""
        print(f"GitHub Account Manager Universal Installer")
        print(f"==========================================")
        print(f"Detected platform: {self.platform}")
        print(f"Admin privileges: {'Yes' if self.is_admin else 'No'}")
        print()
        
        if self.platform == 'windows':
            return self.install_windows()
        elif self.platform == 'darwin':
            return self.install_macos()
        elif self.platform == 'linux':
            return self.install_linux()
        else:
            print(f"❌ Unsupported platform: {self.platform}")
            return False

if __name__ == '__main__':
    installer = UniversalInstaller()
    success = installer.run()
    
    if success:
        print("\\n🎉 Installation completed successfully!")
        print("You can now run GitHub Account Manager from your applications menu or desktop.")
    else:
        print("\\n❌ Installation failed. Please check the requirements and try again.")
    
    input("Press Enter to exit...")
'''
        
        with open('install.py', 'w', encoding='utf-8') as f:
            f.write(installer_script)
        
        # Make executable on Unix systems
        if self.platform != 'Windows':
            os.chmod('install.py', 0o755)
        
        print("✓ Created universal installer (install.py)")

    def create_requirements_files(self):
        """Create requirements files for different platforms"""
        # Base requirements
        base_requirements = [
            "GitPython>=3.1.0",
            "requests>=2.25.0"
        ]
        
        # Windows-specific requirements
        windows_requirements = base_requirements + [
            "pywin32>=227; sys_platform=='win32'",
            "winshell>=0.6; sys_platform=='win32'"
        ]
        
        # Create requirements files
        with open('requirements.txt', 'w') as f:
            f.write('\\n'.join(base_requirements))
        
        with open('requirements-windows.txt', 'w') as f:
            f.write('\\n'.join(windows_requirements))
        
        with open('requirements-dev.txt', 'w') as f:
            f.write('\\n'.join(base_requirements + [
                "pyinstaller>=5.0.0",
                "setuptools>=45.0.0",
                "wheel>=0.36.0"
            ]))
        
        print("✓ Created requirements files")

    def run_build_process(self):
        """Run the complete build process"""
        print(f"GitHub Account Manager Builder")
        print(f"=============================")
        print(f"Platform: {self.platform} {self.arch}")
        print(f"Python: {self.python_version}")
        print()
        
        # Check for source file
        if not os.path.exists('github_account_manager.py'):
            print("❌ github_account_manager.py not found!")
            print("   Please ensure the main Python file is in the current directory.")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Create support files
        self.create_requirements_files()
        self.create_version_info()
        self.create_fixed_spec_file()
        
        # Build executable
        if not self.build_executable():
            return False
        
        # Create installer
        self.create_universal_installer()
        
        # Final summary
        print("\\n" + "="*50)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\\nGenerated files:")
        print(f"  📁 dist/{self.project_name}{'exe' if self.platform == 'Windows' else ''}")
        print(f"  🔧 install.py (universal installer)")
        print(f"  📋 requirements*.txt (dependency lists)")
        print(f"  ⚙️  github_account_manager.spec (build config)")
        
        if self.platform == 'Windows':
            print("\\n🪟 WINDOWS INSTALLATION:")
            print("  1. Run: python install.py")
            print("  2. Or manually copy the exe to your desired location")
        else:
            print(f"\\n🐧 {self.platform.upper()} INSTALLATION:")
            print("  1. Run: python3 install.py")
            print("  2. Follow the prompts to install system-wide")
        
        print("\\n💡 TIPS:")
        print("  - The installer auto-detects your platform")
        print("  - Run with admin/sudo for system-wide installation")
        print("  - Check requirements*.txt for dependencies")
        
        return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--install-only':
        # Just run the installer
        if os.path.exists('install.py'):
            subprocess.run([sys.executable, 'install.py'])
        else:
            print("❌ install.py not found. Run the builder first.")
    else:
        # Run the build process
        builder = GitHubAccountManagerBuilder()
        builder.run_build_process()

if __name__ == "__main__":
    main()