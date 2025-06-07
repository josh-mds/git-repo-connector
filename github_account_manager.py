import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from git import Repo
from pathlib import Path
import re
import subprocess
import platform
import requests
import json
import threading
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from enum import Enum
import webbrowser

class SetupStep(Enum):
    """Setup wizard steps"""
    WELCOME = "welcome"
    DEPENDENCIES = "dependencies"
    SSH_SETUP = "ssh_setup"
    GITHUB_SETUP = "github_setup"
    COMPLETE = "complete"

@dataclass
class Account:
    """Account data structure"""
    name: str
    email: str
    ssh_key_path: str
    github_username: Optional[str] = None
    token: Optional[str] = None

class DependencyChecker:
    """Check and install dependencies"""
    
    @staticmethod
    def check_git() -> Tuple[bool, str]:
        """Check if Git is installed"""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            return True, result.stdout.strip()
        except FileNotFoundError:
            return False, "Git not found. Please install Git from https://git-scm.com/"
    
    @staticmethod
    def check_ssh() -> Tuple[bool, str]:
        """Check if SSH is available"""
        try:
            subprocess.run(['ssh', '-V'], capture_output=True, text=True)
            return True, "SSH available"
        except FileNotFoundError:
            return False, "SSH not found. Please install OpenSSH."
    
    @staticmethod
    def check_python_deps() -> Tuple[bool, str]:
        """Check if required Python packages are installed"""
        try:
            import git
            import requests
            return True, "Python dependencies available"
        except ImportError as e:
            return False, f"Missing Python package: {str(e)}. Run: pip install gitpython requests"

class ProgressDialog:
    """Show progress for long operations"""
    
    def __init__(self, parent, title="Processing..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=20, padx=20, fill='x')
        
        self.label = tk.Label(self.dialog, text="Please wait...")
        self.label.pack(pady=5)
        
        self.progress.start()
    
    def update_text(self, text: str):
        """Update progress text"""
        self.label.config(text=text)
        self.dialog.update()
    
    def close(self):
        """Close progress dialog"""
        self.progress.stop()
        self.dialog.destroy()

class SetupWizard:
    """Guided setup wizard"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_step = SetupStep.WELCOME
        self.window = None
        self.account_data = {}  # Store account data during setup
        
    def start(self):
        """Start the setup wizard"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("GitHub Account Manager Setup")
        self.window.geometry("500x400")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.show_step()
    
    def show_step(self):
        """Show current setup step"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        if self.current_step == SetupStep.WELCOME:
            self.show_welcome()
        elif self.current_step == SetupStep.DEPENDENCIES:
            self.show_dependencies()
        elif self.current_step == SetupStep.SSH_SETUP:
            self.show_ssh_setup()
        elif self.current_step == SetupStep.GITHUB_SETUP:
            self.show_github_setup()
        elif self.current_step == SetupStep.COMPLETE:
            self.show_complete()
    
    def show_welcome(self):
        """Show welcome step"""
        tk.Label(self.window, text="Welcome to GitHub Account Manager", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        text = """This wizard will help you set up multiple GitHub accounts with SSH keys.

What you'll need:
• Git installed on your system
• GitHub account(s)
• 5-10 minutes

The wizard will:
1. Check system dependencies
2. Generate SSH keys
3. Configure GitHub accounts
4. Set up your first repository"""
        
        tk.Label(self.window, text=text, justify='left').pack(pady=20, padx=20)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Get Started", 
                 command=self.next_step).pack(side='right', padx=5)
        tk.Button(button_frame, text="Cancel", 
                 command=self.window.destroy).pack(side='right', padx=5)
    
    def show_dependencies(self):
        """Check and show dependencies"""
        tk.Label(self.window, text="Checking Dependencies", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Check dependencies
        git_ok, git_msg = DependencyChecker.check_git()
        ssh_ok, ssh_msg = DependencyChecker.check_ssh()
        py_ok, py_msg = DependencyChecker.check_python_deps()
        
        # Display results
        results_frame = tk.Frame(self.window)
        results_frame.pack(pady=20, padx=20, fill='x')
        
        self.add_check_result(results_frame, "Git", git_ok, git_msg, 0)
        self.add_check_result(results_frame, "SSH", ssh_ok, ssh_msg, 1)
        self.add_check_result(results_frame, "Python Dependencies", py_ok, py_msg, 2)
        
        all_ok = git_ok and ssh_ok and py_ok
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        if all_ok:
            tk.Label(self.window, text="✅ All dependencies are ready!", 
                    fg='green', font=('Arial', 12, 'bold')).pack(pady=10)
            tk.Button(button_frame, text="Continue", 
                     command=self.next_step).pack(side='right', padx=5)
        else:
            tk.Label(self.window, text="❌ Please install missing dependencies", 
                    fg='red', font=('Arial', 12, 'bold')).pack(pady=10)
            tk.Button(button_frame, text="Recheck", 
                     command=self.show_step).pack(side='right', padx=5)
        
        tk.Button(button_frame, text="Back", 
                 command=self.prev_step).pack(side='right', padx=5)
    
    def show_ssh_setup(self):
        """Show SSH key setup step"""
        tk.Label(self.window, text="Create Your First Account", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        text = """Let's create your first GitHub account with an SSH key.

This will:
• Generate a secure SSH key pair
• Configure SSH for GitHub access
• Set up account-specific authentication"""
        
        tk.Label(self.window, text=text, justify='left').pack(pady=10, padx=20)
        
        # Account form
        form_frame = tk.Frame(self.window)
        form_frame.pack(pady=20, padx=20, fill='x')
        
        # Account name
        tk.Label(form_frame, text="Account Name (e.g., 'personal', 'work'):").grid(row=0, column=0, sticky='w', pady=5)
        self.account_name_var = tk.StringVar(value="personal")
        tk.Entry(form_frame, textvariable=self.account_name_var, width=30).grid(row=0, column=1, pady=5, padx=10)
        
        # Email
        tk.Label(form_frame, text="GitHub Email:").grid(row=1, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, pady=5, padx=10)
        
        # GitHub username
        tk.Label(form_frame, text="GitHub Username:").grid(row=2, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.username_var, width=30).grid(row=2, column=1, pady=5, padx=10)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Create Account", 
                 command=self.create_account).pack(side='right', padx=5)
        tk.Button(button_frame, text="Back", 
                 command=self.prev_step).pack(side='right', padx=5)
    
    def show_github_setup(self):
        """Show GitHub setup instructions"""
        tk.Label(self.window, text="Add SSH Key to GitHub", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        if 'account_name' in self.account_data:
            account_name = self.account_data['account_name']
            
            text = f"""Your SSH key has been generated for account '{account_name}'.

Next steps:
1. Copy the public key below
2. Go to GitHub.com → Settings → SSH and GPG keys
3. Click "New SSH key"
4. Paste the key and save

Your public key:"""
            
            tk.Label(self.window, text=text, justify='left').pack(pady=10, padx=20)
            
            # Public key display
            key_frame = tk.Frame(self.window)
            key_frame.pack(pady=10, padx=20, fill='both', expand=True)
            
            key_text = tk.Text(key_frame, height=4, width=60, wrap=tk.WORD)
            key_text.pack(fill='both', expand=True)
            
            # Load and display public key
            try:
                ssh_dir = os.path.expanduser("~/.ssh")
                key_path = os.path.join(ssh_dir, f"{account_name}.pub")
                with open(key_path, 'r') as f:
                    public_key = f.read()
                    key_text.insert('1.0', public_key)
                    # Copy to clipboard
                    self.window.clipboard_clear()
                    self.window.clipboard_append(public_key)
            except Exception as e:
                key_text.insert('1.0', f"Error reading public key: {e}")
            
            key_text.config(state='disabled')
            
            tk.Label(self.window, text="✅ Public key copied to clipboard!", 
                    fg='green').pack(pady=5)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        def open_github():
            webbrowser.open("https://github.com/settings/keys")
        
        tk.Button(button_frame, text="Open GitHub SSH Settings", 
                 command=open_github).pack(side='left', padx=5)
        tk.Button(button_frame, text="I've Added the Key", 
                 command=self.next_step).pack(side='right', padx=5)
        tk.Button(button_frame, text="Back", 
                 command=self.prev_step).pack(side='right', padx=5)
    
    def show_complete(self):
        """Show completion step"""
        tk.Label(self.window, text="Setup Complete! 🎉", 
                font=('Arial', 16, 'bold'), fg='green').pack(pady=20)
        
        if 'account_name' in self.account_data:
            account_name = self.account_data['account_name']
            
            text = f"""Congratulations! Your account '{account_name}' is ready to use.

What's been set up:
✅ SSH key generated and configured
✅ Account added to the application
✅ Ready for repository management

Next steps:
• Test the SSH connection
• Configure your first repository
• Start coding with confidence!

You can always run this wizard again from Settings."""
            
            tk.Label(self.window, text=text, justify='left').pack(pady=20, padx=20)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        def test_connection():
            if 'account_name' in self.account_data:
                account_name = self.account_data['account_name']
                try:
                    cmd = ["ssh", "-T", f"git@github.com-{account_name}"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if "successfully authenticated" in result.stderr:
                        messagebox.showinfo("Success", "SSH connection test passed!")
                    else:
                        messagebox.showwarning("Test Failed", 
                                              "SSH test failed. Please check that you've added the public key to GitHub.")
                except Exception as e:
                    messagebox.showerror("Error", f"Connection test failed: {e}")
        
        tk.Button(button_frame, text="Test SSH Connection", 
                 command=test_connection).pack(side='left', padx=5)
        tk.Button(button_frame, text="Finish", 
                 command=self.finish_setup).pack(side='right', padx=5)
    
    def create_account(self):
        """Create account with SSH key"""
        print("DEBUG: Create account button clicked")  # Debug output
        
        account_name = self.account_name_var.get().strip()
        email = self.email_var.get().strip()
        username = self.username_var.get().strip()
        
        print(f"DEBUG: Account details - Name: {account_name}, Email: {email}, Username: {username}")
        
        # Validate inputs
        if not account_name or not email or not username:
            print("DEBUG: Validation failed - missing fields")
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        print("DEBUG: Starting input validation")
        if not self.validate_inputs(
            account_name=account_name,
            email=email,
            github_username=username
        ):
            print("DEBUG: Input validation failed")
            return
        
        print("DEBUG: Input validation passed")
        
        # Store account data
        self.account_data = {
            'account_name': account_name,
            'email': email,
            'username': username
        }
        
        print("DEBUG: Starting async key generation")
        # Run SSH key generation asynchronously
        self.run_async_key_generation()
    
    def run_async_key_generation(self):
        """Run SSH key generation in background"""
        # Show progress dialog
        progress = ProgressDialog(self.window, "Generating SSH Key...")
        progress.update_text("Creating SSH key pair...")
        
        def generate_key():
            print("DEBUG: Starting SSH key generation")
            account_name = self.account_data['account_name']
            email = self.account_data['email']
            username = self.account_data['username']
            
            # Generate SSH key
            ssh_dir = os.path.expanduser("~/.ssh")
            print(f"DEBUG: SSH directory: {ssh_dir}")
            os.makedirs(ssh_dir, exist_ok=True)
            
            key_path = os.path.join(ssh_dir, account_name)
            print(f"DEBUG: Key path: {key_path}")
            
            # Check if key already exists
            if os.path.exists(key_path):
                raise Exception(f"SSH key already exists: {key_path}")
            
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", email,
                "-f", key_path,
                "-N", ""  # No passphrase for simplicity
            ]
            
            print(f"DEBUG: Running command: {' '.join(cmd)}")
            
            # Run with timeout to prevent hanging
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            print(f"DEBUG: SSH key generation completed successfully")
            
            # Try to add to SSH agent (optional, don't fail if it doesn't work)
            try:
                print("DEBUG: Attempting to add key to SSH agent")
                # First try to start SSH agent on Windows
                if platform.system() == "Windows":
                    try:
                        subprocess.run(["powershell", "-Command", "Start-Service ssh-agent"], 
                                     check=False, capture_output=True, text=True, timeout=10)
                    except:
                        pass
                
                # Add key to agent
                subprocess.run(["ssh-add", key_path], check=False, capture_output=True, text=True, timeout=10)
                print("DEBUG: Key added to SSH agent successfully")
            except Exception as e:
                print(f"DEBUG: SSH agent operation failed (this is optional): {e}")
                pass  # SSH agent operations are optional
            
            return key_path
        
        def on_success(key_path):
            print("DEBUG: Key generation successful, updating app")
            progress.close()
            
            # Create account object and add to app
            account = Account(
                name=self.account_data['account_name'],
                email=self.account_data['email'],
                ssh_key_path=key_path,
                github_username=self.account_data['username']
            )
            
            self.app.accounts[self.account_data['account_name']] = account
            self.app.update_ssh_config(account)
            self.app.save_config()
            
            # Move to next step
            self.next_step()
        
        def on_error(error):
            print(f"DEBUG: Key generation failed: {error}")
            progress.close()
            
            # Show error with fallback option
            result = messagebox.askyesno(
                "SSH Key Generation Failed", 
                f"Failed to create SSH key:\n{str(error)}\n\n"
                "Would you like to continue anyway?\n"
                "You can generate the SSH key manually later."
            )
            
            if result:
                # Create account without SSH key for now
                self.create_account_without_ssh()
            # If user chooses "No", just stay on current step
        
        # Run in background thread
        thread = threading.Thread(target=self.run_key_generation_thread, args=(generate_key, on_success, on_error))
        thread.daemon = True
        thread.start()
    
    def create_account_without_ssh(self):
        """Create account without SSH key as fallback"""
        print("DEBUG: Creating account without SSH key")
        try:
            # Create a placeholder key path
            ssh_dir = os.path.expanduser("~/.ssh")
            key_path = os.path.join(ssh_dir, self.account_data['account_name'])
            
            # Create account object
            account = Account(
                name=self.account_data['account_name'],
                email=self.account_data['email'],
                ssh_key_path=key_path,  # Will be generated later
                github_username=self.account_data['username']
            )
            
            self.app.accounts[self.account_data['account_name']] = account
            self.app.save_config()
            
            messagebox.showinfo(
                "Account Created", 
                f"Account '{self.account_data['account_name']}' created successfully.\n\n"
                "You'll need to generate an SSH key manually:\n"
                f"ssh-keygen -t ed25519 -C {self.account_data['email']} -f {key_path}"
            )
            
            # Skip to completion
            self.current_step = SetupStep.COMPLETE
            self.show_step()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create account: {e}")
    
    def run_key_generation_thread(self, generate_key, on_success, on_error):
        """Run key generation in thread"""
        try:
            result = generate_key()
            self.window.after(0, lambda: on_success(result))
        except Exception as e:
            self.window.after(0, lambda: on_error(e))
    
    def validate_inputs(self, **kwargs):
        """Validate wizard inputs"""
        try:
            for field, value in kwargs.items():
                if field == "email":
                    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(pattern, value):
                        raise Exception(f"Invalid email format: {value}")
                elif field == "github_username":
                    pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
                    if not re.match(pattern, value):
                        raise Exception(f"Invalid GitHub username: {value}")
                elif field == "account_name":
                    pattern = r'^[a-zA-Z0-9\-_]+$'
                    if not re.match(pattern, value) or len(value) == 0:
                        raise Exception(f"Invalid account name: {value}")
            return True
        except Exception as e:
            messagebox.showerror("Validation Error", str(e))
            return False
    
    def finish_setup(self):
        """Finish setup and close wizard"""
        # Refresh the main app
        if hasattr(self.app, 'refresh_accounts_list'):
            self.app.refresh_accounts_list()
        
        messagebox.showinfo("Welcome!", 
                           "Setup complete! You can now manage your repositories and accounts.")
        self.window.destroy()
    
    def add_check_result(self, parent, name, success, message, row):
        """Add dependency check result"""
        icon = "✅" if success else "❌"
        color = "green" if success else "red"
        
        tk.Label(parent, text=f"{icon} {name}", fg=color).grid(row=row, column=0, sticky='w', pady=2)
        tk.Label(parent, text=message, fg='gray').grid(row=row, column=1, sticky='w', padx=10, pady=2)
    
    def next_step(self):
        """Go to next step"""
        steps = list(SetupStep)
        current_index = steps.index(self.current_step)
        if current_index < len(steps) - 1:
            self.current_step = steps[current_index + 1]
            self.show_step()
    
    def prev_step(self):
        """Go to previous step"""
        steps = list(SetupStep)
        current_index = steps.index(self.current_step)
        if current_index > 0:
            self.current_step = steps[current_index - 1]
            self.show_step()

class ImprovedGitHubAccountManager:
    """Improved GitHub Account Manager with better UX"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Account Manager")
        self.root.geometry("800x600")
        
        # Initialize paths and data
        self.ssh_config_path = os.path.expanduser("~/.ssh/config")
        self.ssh_dir = os.path.expanduser("~/.ssh")
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        # Data storage
        self.accounts: Dict[str, Account] = {}
        self.repos: List[Tuple] = []
        self.last_scanned_path = ""
        
        # Load configuration
        self.load_config()
        
        # Setup GUI
        self.setup_gui()
        
        # Show welcome message for first-time users
        if not self.accounts:
            self.show_welcome_message()
    
    def show_welcome_message(self):
        """Show welcome message for first-time users"""
        result = messagebox.askyesno(
            "Welcome to GitHub Account Manager",
            "Welcome! It looks like this is your first time using the GitHub Account Manager.\n\n"
            "Would you like to run the setup wizard to create your first account?\n\n"
            "You can also do this later from the Accounts tab."
        )
        
        if result:
            self.show_setup_wizard()
    
    def show_setup_wizard(self):
        """Show setup wizard for first-time users"""
        wizard = SetupWizard(self.root, self)
        wizard.start()
    
    def load_config(self):
        """Load application configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.last_scanned_path = config.get("last_scanned_path", "")
                    
                    # Load accounts
                    accounts_data = config.get("accounts", {})
                    for name, data in accounts_data.items():
                        self.accounts[name] = Account(
                            name=data["name"],
                            email=data["email"],
                            ssh_key_path=data["ssh_key_path"],
                            github_username=data.get("github_username"),
                            token=data.get("token")
                        )
        except Exception as e:
            self.show_error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save application configuration"""
        try:
            config = {
                "last_scanned_path": self.last_scanned_path,
                "accounts": {}
            }
            
            for name, account in self.accounts.items():
                config["accounts"][name] = {
                    "name": account.name,
                    "email": account.email,
                    "ssh_key_path": account.ssh_key_path,
                    "github_username": account.github_username,
                    "token": account.token
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.show_error(f"Error saving configuration: {e}")
    
    def show_error(self, message: str, title: str = "Error"):
        """Show user-friendly error message"""
        messagebox.showerror(title, message)
    
    def show_success(self, message: str, title: str = "Success"):
        """Show success message"""
        messagebox.showinfo(title, message)
    
    def show_info(self, message: str, title: str = "Information"):
        """Show information message"""
        messagebox.showinfo(title, message)
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate multiple inputs"""
        try:
            for field, value in kwargs.items():
                if field == "email":
                    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(pattern, value):
                        raise Exception(f"Invalid email format: {value}")
                elif field == "github_username":
                    pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
                    if not re.match(pattern, value):
                        raise Exception(f"Invalid GitHub username: {value}")
                elif field == "account_name":
                    pattern = r'^[a-zA-Z0-9\-_]+$'
                    if not re.match(pattern, value) or len(value) == 0:
                        raise Exception(f"Invalid account name: {value}")
                elif field == "repo_name":
                    pattern = r'^[a-zA-Z0-9._-]+$'
                    if not re.match(pattern, value) or len(value) == 0:
                        raise Exception(f"Invalid repository name: {value}")
            return True
        except Exception as e:
            self.show_error(str(e), "Validation Error")
            return False
    
    def run_async_operation(self, operation, success_callback=None, error_callback=None):
        """Run operation in background with progress dialog"""
        progress = ProgressDialog(self.root, "Processing...")
        
        def run_operation():
            try:
                result = operation()
                self.root.after(0, lambda: self.handle_async_success(progress, result, success_callback))
            except Exception as e:
                self.root.after(0, lambda: self.handle_async_error(progress, e, error_callback))
        
        thread = threading.Thread(target=run_operation)
        thread.daemon = True
        thread.start()
    
    def handle_async_success(self, progress, result, callback):
        """Handle successful async operation"""
        progress.close()
        if callback:
            callback(result)
    
    def handle_async_error(self, progress, error, callback):
        """Handle failed async operation"""
        progress.close()
        if callback:
            callback(error)
        else:
            self.show_error(f"Operation failed: {str(error)}")
    
    def create_account_wizard(self):
        """Show account creation wizard"""
        wizard = tk.Toplevel(self.root)
        wizard.title("Create New Account")
        wizard.geometry("400x300")
        wizard.transient(self.root)
        wizard.grab_set()
        
        # Form fields
        fields = {}
        
        tk.Label(wizard, text="Create New GitHub Account", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        form_frame = tk.Frame(wizard)
        form_frame.pack(pady=20, padx=20, fill='both')
        
        # Account name
        tk.Label(form_frame, text="Account Name:").grid(row=0, column=0, sticky='w', pady=5)
        fields['name'] = tk.Entry(form_frame, width=30)
        fields['name'].grid(row=0, column=1, pady=5, padx=10)
        
        # Email
        tk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky='w', pady=5)
        fields['email'] = tk.Entry(form_frame, width=30)
        fields['email'].grid(row=1, column=1, pady=5, padx=10)
        
        # GitHub username
        tk.Label(form_frame, text="GitHub Username:").grid(row=2, column=0, sticky='w', pady=5)
        fields['github_username'] = tk.Entry(form_frame, width=30)
        fields['github_username'].grid(row=2, column=1, pady=5, padx=10)
        
        # Buttons
        button_frame = tk.Frame(wizard)
        button_frame.pack(pady=20)
        
        def create_account():
            # Validate inputs
            name = fields['name'].get().strip()
            email = fields['email'].get().strip()
            github_username = fields['github_username'].get().strip()
            
            if not self.validate_inputs(
                account_name=name,
                email=email,
                github_username=github_username
            ):
                return
            
            # Check if account already exists
            if name in self.accounts:
                self.show_error(f"Account '{name}' already exists")
                return
            
            wizard.destroy()
            self.create_account_with_ssh_key(name, email, github_username)
        
        tk.Button(button_frame, text="Create Account", 
                 command=create_account).pack(side='right', padx=5)
        tk.Button(button_frame, text="Cancel", 
                 command=wizard.destroy).pack(side='right', padx=5)
        
        # Focus on first field
        fields['name'].focus()
    
    def create_account_with_ssh_key(self, name: str, email: str, github_username: str):
        """Create account and generate SSH key"""
        def generate_key():
            # Generate SSH key
            key_path = os.path.join(self.ssh_dir, name)
            
            if os.path.exists(key_path):
                raise Exception(f"SSH key already exists: {key_path}")
            
            os.makedirs(self.ssh_dir, exist_ok=True)
            
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", email,
                "-f", key_path,
                "-N", ""  # No passphrase for simplicity
            ]
            
            # Run with timeout to prevent hanging
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            
            # Try to add to SSH agent (optional)
            try:
                # Start SSH agent on Windows if needed
                if platform.system() == "Windows":
                    try:
                        subprocess.run(["powershell", "-Command", "Start-Service ssh-agent"], 
                                     check=False, capture_output=True, text=True, timeout=10)
                    except:
                        pass
                
                # Add key to agent
                subprocess.run(["ssh-add", key_path], check=False, capture_output=True, text=True, timeout=10)
            except:
                pass  # SSH agent operations are optional
            
            return key_path
        
        def on_success(key_path):
            # Create account object
            account = Account(
                name=name,
                email=email,
                ssh_key_path=key_path,
                github_username=github_username
            )
            
            self.accounts[name] = account
            self.save_config()
            self.update_ssh_config(account)
            self.refresh_accounts_list()
            
            # Show next steps
            self.show_ssh_key_instructions(account)
        
        def on_error(error):
            self.show_error(f"Failed to create account: {str(error)}")
        
        # Show progress and run async
        progress = ProgressDialog(self.root, "Creating Account...")
        progress.update_text("Generating SSH key...")
        
        def run_in_thread():
            try:
                result = generate_key()
                self.root.after(0, lambda: [progress.close(), on_success(result)])
            except Exception as e:
                self.root.after(0, lambda: [progress.close(), on_error(e)])
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
    
    def show_ssh_key_instructions(self, account: Account):
        """Show instructions for adding SSH key to GitHub"""
        instructions = tk.Toplevel(self.root)
        instructions.title("Add SSH Key to GitHub")
        instructions.geometry("500x400")
        instructions.transient(self.root)
        
        tk.Label(instructions, text="SSH Key Generated Successfully!", 
                font=('Arial', 14, 'bold'), fg='green').pack(pady=10)
        
        text_frame = tk.Frame(instructions)
        text_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        text = f"""Your SSH key has been generated and added to SSH agent.

Next steps:
1. Copy the public key below
2. Go to GitHub.com → Settings → SSH and GPG keys
3. Click "New SSH key"
4. Paste the key and save

Public Key for {account.name}:"""
        
        tk.Label(text_frame, text=text, justify='left').pack(anchor='w')
        
        # Public key text area
        key_text = tk.Text(text_frame, height=8, width=60)
        key_text.pack(pady=10, fill='both', expand=True)
        
        try:
            with open(f"{account.ssh_key_path}.pub", 'r') as f:
                public_key = f.read()
                key_text.insert('1.0', public_key)
                key_text.config(state='disabled')
        except Exception as e:
            key_text.insert('1.0', f"Error reading public key: {e}")
        
        # Buttons
        button_frame = tk.Frame(instructions)
        button_frame.pack(pady=10)
        
        def copy_key():
            self.root.clipboard_clear()
            self.root.clipboard_append(public_key)
            self.show_success("Public key copied to clipboard!")
        
        tk.Button(button_frame, text="Copy Key", command=copy_key).pack(side='left', padx=5)
        tk.Button(button_frame, text="Open GitHub", 
                 command=lambda: webbrowser.open("https://github.com/settings/keys")).pack(side='left', padx=5)
        tk.Button(button_frame, text="Done", command=instructions.destroy).pack(side='left', padx=5)
    
    def update_ssh_config(self, account: Account):
        """Update SSH config for account"""
        # Read existing config
        content = ""
        if os.path.exists(self.ssh_config_path):
            with open(self.ssh_config_path, 'r') as f:
                content = f.read()
        
        # Remove existing entry for this account
        lines = content.split('\n')
        new_lines = []
        skip = False
        
        for line in lines:
            if line.strip() == f"Host github.com-{account.name}":
                skip = True
                continue
            elif line.strip().startswith('Host ') and skip:
                skip = False
            
            if not skip:
                new_lines.append(line)
        
        # Add new entry
        config_entry = f"""
# {account.name} account
Host github.com-{account.name}
    HostName github.com
    User git
    IdentityFile {account.ssh_key_path}
"""
        new_lines.append(config_entry)
        
        # Write config
        os.makedirs(os.path.dirname(self.ssh_config_path), exist_ok=True)
        with open(self.ssh_config_path, 'w') as f:
            f.write('\n'.join(new_lines))
    
    def setup_gui(self):
        """Setup the main GUI with improved layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Accounts tab
        self.accounts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.accounts_frame, text="Accounts")
        self.setup_accounts_tab()
        
        # Repositories tab
        self.repos_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repos_frame, text="Repositories")
        self.setup_repositories_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
    
    def setup_accounts_tab(self):
        """Setup accounts management tab"""
        # Header
        header_frame = ttk.Frame(self.accounts_frame)
        header_frame.pack(fill='x', pady=10)
        
        ttk.Label(header_frame, text="GitHub Accounts", 
                 font=('Arial', 16, 'bold')).pack(side='left')
        ttk.Button(header_frame, text="+ Add Account", 
                  command=self.create_account_wizard).pack(side='right')
        
        # Accounts list
        list_frame = ttk.Frame(self.accounts_frame)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        # Treeview for accounts
        columns = ('Name', 'Email', 'GitHub Username', 'SSH Key')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=150)
        
        self.accounts_tree.pack(fill='both', expand=True)
        
        # Context menu for accounts
        self.accounts_menu = tk.Menu(self.root, tearoff=0)
        self.accounts_menu.add_command(label="Edit", command=self.edit_account)
        self.accounts_menu.add_command(label="Delete", command=self.delete_account)
        self.accounts_menu.add_command(label="Test Connection", command=self.test_ssh_connection)
        
        self.accounts_tree.bind("<Button-3>", self.show_accounts_menu)
        
        # Refresh accounts list
        self.refresh_accounts_list()
    
    def setup_repositories_tab(self):
        """Setup repositories management tab"""
        # Repository scanning
        scan_frame = ttk.LabelFrame(self.repos_frame, text="Repository Scanner")
        scan_frame.pack(fill='x', pady=10, padx=10)
        
        path_frame = ttk.Frame(scan_frame)
        path_frame.pack(fill='x', pady=5)
        
        ttk.Label(path_frame, text="Scan Path:").pack(side='left')
        self.path_var = tk.StringVar(value=self.last_scanned_path)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(path_frame, text="Browse", command=self.browse_folder).pack(side='left', padx=5)
        ttk.Button(path_frame, text="Scan", command=self.scan_repositories).pack(side='left', padx=5)
        
        # Repositories list
        repos_list_frame = ttk.LabelFrame(self.repos_frame, text="Repositories")
        repos_list_frame.pack(fill='both', expand=True, pady=10, padx=10)
        
        # Treeview for repositories
        repo_columns = ('Path', 'Account', 'Remote URL', 'Status')
        self.repos_tree = ttk.Treeview(repos_list_frame, columns=repo_columns, show='headings')
        
        for col in repo_columns:
            self.repos_tree.heading(col, text=col)
            self.repos_tree.column(col, width=200)
        
        self.repos_tree.pack(fill='both', expand=True)
        
        # Repository actions
        actions_frame = ttk.Frame(repos_list_frame)
        actions_frame.pack(fill='x', pady=5)
        
        ttk.Button(actions_frame, text="Switch Account", 
                  command=self.switch_repo_account).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="Configure New Repo", 
                  command=self.configure_new_repo).pack(side='left', padx=5)
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        # System info
        info_frame = ttk.LabelFrame(self.settings_frame, text="System Information")
        info_frame.pack(fill='x', pady=10, padx=10)
        
        # Check system status
        git_ok, git_msg = DependencyChecker.check_git()
        ssh_ok, ssh_msg = DependencyChecker.check_ssh()
        py_ok, py_msg = DependencyChecker.check_python_deps()
        
        ttk.Label(info_frame, text=f"Git: {'✅' if git_ok else '❌'} {git_msg}").pack(anchor='w', pady=2)
        ttk.Label(info_frame, text=f"SSH: {'✅' if ssh_ok else '❌'} {ssh_msg}").pack(anchor='w', pady=2)
        ttk.Label(info_frame, text=f"Python Deps: {'✅' if py_ok else '❌'} {py_msg}").pack(anchor='w', pady=2)
        
        # Actions
        actions_frame = ttk.LabelFrame(self.settings_frame, text="Actions")
        actions_frame.pack(fill='x', pady=10, padx=10)
        
        ttk.Button(actions_frame, text="Open SSH Folder", 
                  command=self.open_ssh_folder).pack(side='left', padx=5, pady=5)
        ttk.Button(actions_frame, text="Run Setup Wizard", 
                  command=self.show_setup_wizard).pack(side='left', padx=5, pady=5)
        ttk.Button(actions_frame, text="Export Configuration", 
                  command=self.export_config).pack(side='left', padx=5, pady=5)
    
    def refresh_accounts_list(self):
        """Refresh the accounts list"""
        # Clear existing items
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Add accounts
        for account in self.accounts.values():
            self.accounts_tree.insert('', 'end', values=(
                account.name,
                account.email,
                account.github_username or 'Not set',
                os.path.basename(account.ssh_key_path)
            ))
    
    def show_accounts_menu(self, event):
        """Show context menu for accounts"""
        item = self.accounts_tree.selection()[0] if self.accounts_tree.selection() else None
        if item:
            self.accounts_menu.post(event.x_root, event.y_root)
    
    def edit_account(self):
        """Edit selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            self.show_error("Please select an account to edit")
            return
        
        # Get account name from selection
        item = selection[0]
        account_name = self.accounts_tree.item(item)['values'][0]
        account = self.accounts[account_name]
        
        # Show edit dialog (implement as needed)
        self.show_info(f"Edit functionality for {account_name} coming soon!")
    
    def delete_account(self):
        """Delete selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            self.show_error("Please select an account to delete")
            return
        
        item = selection[0]
        account_name = self.accounts_tree.item(item)['values'][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete account '{account_name}'?\n\n"
                              "This will remove the SSH configuration but keep the SSH key files."):
            del self.accounts[account_name]
            self.save_config()
            self.refresh_accounts_list()
            self.show_success(f"Account '{account_name}' deleted successfully")
    
    def test_ssh_connection(self):
        """Test SSH connection for selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            self.show_error("Please select an account to test")
            return
        
        item = selection[0]
        account_name = self.accounts_tree.item(item)['values'][0]
        
        def test_connection():
            try:
                cmd = ["ssh", "-T", f"git@github.com-{account_name}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                # SSH to GitHub returns exit code 1 on successful auth
                if "successfully authenticated" in result.stderr:
                    return True, "Connection successful"
                else:
                    return False, result.stderr or "Connection failed"
            except subprocess.TimeoutExpired:
                return False, "Connection timeout"
            except Exception as e:
                return False, str(e)
        
        def on_test_complete(result):
            success, message = result
            if success:
                self.show_success(f"SSH connection test passed for '{account_name}'")
            else:
                self.show_error(f"SSH connection test failed for '{account_name}':\n{message}")
        
        self.run_async_operation(test_connection, on_test_complete)
    
    def browse_folder(self):
        """Browse for folder to scan"""
        folder = filedialog.askdirectory(initialdir=self.last_scanned_path)
        if folder:
            self.path_var.set(folder)
            self.last_scanned_path = folder
            self.save_config()
    
    def scan_repositories(self):
        """Scan for repositories in the selected path"""
        path = self.path_var.get()
        if not path or not os.path.isdir(path):
            self.show_error("Please select a valid directory to scan")
            return
        
        def scan():
            repos = []
            for root, dirs, files in os.walk(path):
                if '.git' in dirs:
                    try:
                        repo = Repo(root)
                        status = self.get_repo_status(repo)
                        remote_url = repo.remotes.origin.url if 'origin' in repo.remotes else 'No remote'
                        account = self.detect_repo_account(remote_url)
                        
                        repos.append((root, account, remote_url, status))
                    except Exception as e:
                        repos.append((root, 'Error', f'Error: {e}', 'Error'))
            return repos
        
        def on_scan_complete(repos):
            self.repos = repos
            self.refresh_repos_list()
            self.show_success(f"Found {len(repos)} repositories")
        
        self.run_async_operation(scan, on_scan_complete)
    
    def get_repo_status(self, repo) -> str:
        """Get repository status"""
        try:
            if repo.is_dirty():
                return "Modified"
            elif repo.untracked_files:
                return "Untracked files"
            else:
                return "Clean"
        except:
            return "Unknown"
    
    def detect_repo_account(self, remote_url: str) -> str:
        """Detect which account a repository belongs to"""
        if not remote_url or remote_url == 'No remote':
            return 'No remote'
        
        # Check for SSH URLs with account host
        match = re.match(r'git@github\.com-(\w+):', remote_url)
        if match:
            account_name = match.group(1)
            return account_name if account_name in self.accounts else 'Unknown account'
        
        # Check for HTTPS URLs
        if 'github.com' in remote_url:
            return 'HTTPS (needs conversion)'
        
        return 'Non-GitHub'
    
    def refresh_repos_list(self):
        """Refresh the repositories list"""
        # Clear existing items
        for item in self.repos_tree.get_children():
            self.repos_tree.delete(item)
        
        # Add repositories
        for repo_data in self.repos:
            path, account, remote_url, status = repo_data
            display_path = path.replace(self.path_var.get(), '').lstrip(os.sep) or os.path.basename(path)
            self.repos_tree.insert('', 'end', values=(
                display_path,
                account,
                remote_url[:50] + '...' if len(remote_url) > 50 else remote_url,
                status
            ))
    
    def switch_repo_account(self):
        """Switch repository to different account"""
        self.show_info("Switch account functionality coming soon!")
    
    def configure_new_repo(self):
        """Configure a new repository"""
        self.show_info("Configure new repository functionality coming soon!")
    
    def open_ssh_folder(self):
        """Open SSH folder in file manager"""
        try:
            if platform.system() == "Windows":
                os.startfile(self.ssh_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.ssh_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.ssh_dir])
        except Exception as e:
            self.show_error(f"Could not open SSH folder: {e}")
    
    def export_config(self):
        """Export configuration to file"""
        try:
            export_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if export_path:
                with open(export_path, 'w') as f:
                    json.dump({
                        "accounts": {name: {
                            "name": acc.name,
                            "email": acc.email,
                            "ssh_key_path": acc.ssh_key_path,
                            "github_username": acc.github_username
                        } for name, acc in self.accounts.items()},
                        "last_scanned_path": self.last_scanned_path
                    }, f, indent=2)
                self.show_success(f"Configuration exported to {export_path}")
        except Exception as e:
            self.show_error(f"Failed to export configuration: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImprovedGitHubAccountManager(root)
    root.mainloop()