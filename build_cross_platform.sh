#!/bin/bash

# Cross-platform build script for GitHub Account Manager
# This script provides alternatives for iOS and other platforms

echo "GitHub Account Manager - Cross-Platform Build Script"
echo "===================================================="

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="Windows"
else
    PLATFORM="Unknown"
fi

echo "Detected platform: $PLATFORM"

# Function to create web application version
create_web_app() {
    echo "Creating web application version..."
    
    # Create web app directory
    mkdir -p web_app
    cd web_app
    
    # Create Flask wrapper
    cat > app.py << 'EOL'
from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.append('..')
from github_account_manager import GitHubAccountManager
import tkinter as tk

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan_repos', methods=['POST'])
def scan_repos():
    # This would need to be adapted for web interface
    # Currently just returns mock data
    return jsonify({
        'repos': [],
        'status': 'success',
        'message': 'Web version not fully implemented'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
EOL
    
    # Create templates directory
    mkdir -p templates
    
    # Create basic HTML template
    cat > templates/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Account Manager</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>GitHub Account Manager - Web Version</h1>
    <p>This is a web-based version of the GitHub Account Manager.</p>
    <p>The full desktop functionality is available in the native application.</p>
    
    <div id="status">
        <h2>Note:</h2>
        <p>This web version is a placeholder for cross-platform compatibility.</p>
        <p>For full functionality, use the desktop application on Windows/Linux/macOS.</p>
    </div>
</body>
</html>
EOL
    
    echo "✓ Web application template created in web_app/"
    cd ..
}

# Function to create Android build configuration
create_android_config() {
    echo "Creating Android build configuration..."
    
    # Create buildozer.spec for Android builds
    cat > buildozer.spec << 'EOL'
[app]
title = GitHub Account Manager
package.name = githubaccountmanager
package.domain = com.example.githubaccountmanager

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3,kivy,gitpython,requests

[buildozer]
log_level = 2

[app:android]
archs = arm64-v8a, armeabi-v7a

# Note: This requires significant modifications to work with Kivy
# The tkinter GUI would need to be completely rewritten
EOL
    
    echo "✓ Android build configuration created (buildozer.spec)"
    echo "  Note: Requires complete rewrite of GUI using Kivy"
}

# Function to create iOS build instructions
create_ios_instructions() {
    echo "Creating iOS build instructions..."
    
    cat > ios_build_instructions.md << 'EOL'
# iOS Build Instructions

## Important Note
iOS does not support traditional executable files like Windows .exe files.
To run Python applications on iOS, you have several options:

## Option 1: Pythonista (Recommended for Simple Scripts)
1. Install Pythonista from the App Store
2. Transfer the Python script to Pythonista
3. Note: Limited functionality due to iOS sandboxing

## Option 2: Convert to Native iOS App
This requires significant development work:

### Requirements:
- macOS with Xcode
- iOS Developer Account
- Complete rewrite of the GUI using:
  - Kivy + kivy-ios
  - BeeWare (Briefcase)
  - React Native with Python bridge

### Steps for Kivy approach:
1. Install kivy-ios:
   ```bash
   pip install kivy-ios
   ```

2. Rewrite the GUI using Kivy instead of tkinter

3. Build iOS package:
   ```bash
   toolchain build python3 kivy
   toolchain create <app_name> <app_directory>
   ```

## Option 3: Web Application (Universal)
Create a web-based version that works on any device:
1. Use Flask/FastAPI for backend
2. Create responsive web interface
3. Deploy to cloud service
4. Access via Safari on iOS

## Option 4: Remote Desktop Solution
- Use app like TeamViewer or Chrome Remote Desktop
- Run the Windows executable on a server
- Access remotely from iOS device

## Recommendation
For iOS compatibility, we recommend creating a web-based version
of the application that can be accessed through Safari.
EOL
    
    echo "✓ iOS build instructions created (ios_build_instructions.md)"
}

# Function to create universal installer
create_universal_installer() {
    echo "Creating universal installer script..."
    
    cat > install.sh << 'EOL'
#!/bin/bash

# Universal installer for GitHub Account Manager

echo "GitHub Account Manager - Universal Installer"
echo "==========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Please install Python 3.7 or later from https://python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $python_version detected"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "⚠️  Git is not installed"
    echo "Please install Git from https://git-scm.com"
    echo "Git is required for the application to function properly"
fi

# Create desktop shortcut (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Creating desktop shortcut..."
    cat > ~/Desktop/github-account-manager.desktop << EOF
[Desktop Entry]
Name=GitHub Account Manager
Comment=Manage GitHub accounts and repositories
Exec=python3 $(pwd)/github_account_manager.py
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;
EOF
    chmod +x ~/Desktop/github-account-manager.desktop
    echo "✓ Desktop shortcut created"
fi

echo ""
echo "Installation complete!"
echo "Run the application with: python3 github_account_manager.py"
EOL
    
    chmod +x install.sh
    echo "✓ Universal installer created (install.sh)"
}

# Main execution
main() {
    case $1 in
        "web")
            create_web_app
            ;;
        "android")
            create_android_config
            ;;
        "ios")
            create_ios_instructions
            ;;
        "installer")
            create_universal_installer
            ;;
        "all")
            create_web_app
            create_android_config
            create_ios_instructions
            create_universal_installer
            echo ""
            echo "All platform configurations created!"
            ;;
        *)
            echo "Usage: $0 [web|android|ios|installer|all]"
            echo ""
            echo "Options:"
            echo "  web       - Create web application template"
            echo "  android   - Create Android build configuration"
            echo "  ios       - Create iOS build instructions"
            echo "  installer - Create universal installer script"
            echo "  all       - Create all platform configurations"
            echo ""
            echo "For Windows executable, run setup.py on Windows"
            ;;
    esac
}

main $1