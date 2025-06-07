#!/usr/bin/env python3
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
        print("\n🎉 Installation completed successfully!")
        print("You can now run GitHub Account Manager from your applications menu or desktop.")
    else:
        print("\n❌ Installation failed. Please check the requirements and try again.")
    
    input("Press Enter to exit...")
