import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import tkinter.font
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
    """Show progress for long operations - FIXED VERSION"""
    
    def __init__(self, parent, title="Processing..."):
        print(f"DEBUG: Creating progress dialog: {title}")
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
        self.closed = False
        print("DEBUG: Progress dialog created successfully")
    
    def update_text(self, text: str):
        """Update progress text"""
        if not self.closed and self.dialog.winfo_exists():
            self.label.config(text=text)
            self.dialog.update()
    
    def close(self):
        """Close progress dialog"""
        print("DEBUG: Attempting to close progress dialog")
        if not self.closed:
            try:
                self.progress.stop()
                self.dialog.grab_release()
                self.dialog.destroy()
                self.closed = True
                print("DEBUG: Progress dialog closed successfully")
            except Exception as e:
                print(f"DEBUG: Error closing progress dialog: {e}")
                self.closed = True
class SetupWizard:
    """Guided setup wizard - FIXED VERSION"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_step = SetupStep.WELCOME
        self.window = None
        self.account_data = {}
        
    def start(self):
        """Start the setup wizard"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("GitHub Account Manager Setup")
        self.window.geometry("500x450")  # Increased height for token field
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.show_step()
    
    def show_step(self):
        """Show current setup step"""
        print(f"DEBUG: show_step() called for step: {self.current_step}")
        
        # Clear window
        try:
            for widget in self.window.winfo_children():
                widget.destroy()
            print("DEBUG: Window cleared successfully")
        except Exception as e:
            print(f"DEBUG: Error clearing window: {e}")
        
        try:
            if self.current_step == SetupStep.WELCOME:
                print("DEBUG: Showing welcome step")
                self.show_welcome()
            elif self.current_step == SetupStep.DEPENDENCIES:
                print("DEBUG: Showing dependencies step")
                self.show_dependencies()
            elif self.current_step == SetupStep.SSH_SETUP:
                print("DEBUG: Showing SSH setup step")
                self.show_ssh_setup()
            elif self.current_step == SetupStep.GITHUB_SETUP:
                print("DEBUG: Showing GitHub setup step")
                self.show_github_setup()
            elif self.current_step == SetupStep.COMPLETE:
                print("DEBUG: Showing complete step")
                self.show_complete()
            print(f"DEBUG: Step {self.current_step} displayed successfully")
        except Exception as e:
            print(f"DEBUG: Error showing step {self.current_step}: {e}")
            messagebox.showerror("Error", f"Failed to display step: {e}")
    
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
        
        # GitHub token (optional)
        tk.Label(form_frame, text="GitHub Token (Optional):").grid(row=3, column=0, sticky='w', pady=5)
        self.token_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.token_var, width=30, show="*").grid(row=3, column=1, pady=5, padx=10)
        
        # Help text
        help_text = """💡 Adding a token enables automatic repository creation
Generate at: GitHub.com → Settings → Developer settings → Personal access tokens"""
        tk.Label(form_frame, text=help_text, font=('Arial', 8), fg='gray', justify='left').grid(
            row=4, column=0, columnspan=2, sticky='w', pady=10)
        
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
        print("DEBUG: Create account button clicked")
        
        account_name = self.account_name_var.get().strip()
        email = self.email_var.get().strip()
        username = self.username_var.get().strip()
        token = self.token_var.get().strip()
        
        print(f"DEBUG: Account details - Name: {account_name}, Email: {email}, Username: {username}")
        
        # Validate inputs
        if not account_name or not email or not username:
            print("DEBUG: Validation failed - missing fields")
            messagebox.showerror("Error", "Please fill in all required fields (token is optional)")
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
            'username': username,
            'token': token
        }
        
        print("DEBUG: Starting async key generation")
        # Run SSH key generation asynchronously
        self.run_async_key_generation()
    
    def run_async_key_generation(self):
        """Run SSH key generation in background - FIXED VERSION"""
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
            try:
                progress.close()
                print("DEBUG: Progress dialog closed")
                
                # Create account object and add to app
                account = Account(
                    name=self.account_data['account_name'],
                    email=self.account_data['email'],
                    ssh_key_path=key_path,
                    github_username=self.account_data['username'],
                    token=self.account_data['token'] if self.account_data['token'] else None
                )
                print("DEBUG: Account object created")
                
                self.app.accounts[self.account_data['account_name']] = account
                print("DEBUG: Account added to app.accounts")
                
                self.app.update_ssh_config(account)
                print("DEBUG: SSH config updated")
                
                self.app.save_config()
                print("DEBUG: App config saved")
                
                # Move to next step
                print("DEBUG: About to call next_step()")
                self.next_step()
                print("DEBUG: next_step() completed")
                
            except Exception as e:
                print(f"DEBUG: Error in on_success: {e}")
                messagebox.showerror("Error", f"Failed to update application: {e}")
        
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
        def run_generation_thread():
            try:
                print("DEBUG: Thread started")
                result = generate_key()
                print(f"DEBUG: Thread completed successfully, scheduling UI callback")
                # FIX: Capture result with default parameter
                if self.window and self.window.winfo_exists():
                    self.window.after_idle(lambda r=result: on_success(r))
                else:
                    print("DEBUG: Window no longer exists")
            except Exception as error:
                print(f"DEBUG: Thread failed with error: {error}")
                # FIX: Capture error with default parameter
                if self.window and self.window.winfo_exists():
                    self.window.after_idle(lambda e=error: on_error(e))
                else:
                    print("DEBUG: Window no longer exists for error callback")
        
        thread = threading.Thread(target=run_generation_thread)
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
                github_username=self.account_data['username'],
                token=self.account_data['token'] if self.account_data['token'] else None
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
        print(f"DEBUG: next_step() called, current step: {self.current_step}")
        steps = list(SetupStep)
        current_index = steps.index(self.current_step)
        print(f"DEBUG: Current step index: {current_index}")
        
        if current_index < len(steps) - 1:
            self.current_step = steps[current_index + 1]
            print(f"DEBUG: Moving to next step: {self.current_step}")
            try:
                self.show_step()
                print("DEBUG: show_step() completed")
            except Exception as e:
                print(f"DEBUG: Error in show_step(): {e}")
                messagebox.showerror("Error", f"Failed to show next step: {e}")
        else:
            print("DEBUG: Already at last step")
    
    def prev_step(self):
        """Go to previous step"""
        steps = list(SetupStep)
        current_index = steps.index(self.current_step)
        if current_index > 0:
            self.current_step = steps[current_index - 1]
            self.show_step()
class ImprovedGitHubAccountManager:
    """Improved GitHub Account Manager with better UX - FIXED VERSION"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Account Manager")
        self.root.geometry("1000x750")  # Increased width for token status column
        
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
    
    def safe_async_operation(self, operation_func, success_callback=None, error_callback=None, progress_title="Processing..."):
        """
        Safe wrapper for async operations that handles closure issues properly - FIXED VERSION
        
        Args:
            operation_func: Function to run in background
            success_callback: Function to call on success (receives result)
            error_callback: Function to call on error (receives error)
            progress_title: Title for progress dialog
        """
        progress = ProgressDialog(self.root, progress_title)
        
        def run_operation():
            try:
                result = operation_func()
                # FIX: Use default parameter to capture result
                self.root.after(0, lambda r=result: self._handle_async_success(progress, r, success_callback))
            except Exception as error:
                # FIX: Use default parameter to capture error
                self.root.after(0, lambda e=error: self._handle_async_error(progress, e, error_callback))
        
        thread = threading.Thread(target=run_operation)
        thread.daemon = True
        thread.start()
    
    def _handle_async_success(self, progress, result, callback):
        """Handle successful async operation"""
        try:
            progress.close()
            if callback:
                callback(result)
        except Exception as e:
            self.show_error(f"Error handling success: {e}")

    def _handle_async_error(self, progress, error, callback):
        """Handle failed async operation"""
        try:
            progress.close()
            if callback:
                callback(error)
            else:
                self.show_error(f"Operation failed: {str(error)}")
        except Exception as e:
            self.show_error(f"Error handling failure: {e}")
    
    def run_async_operation(self, operation, success_callback=None, error_callback=None):
        """Run operation in background with progress dialog - FIXED VERSION"""
        progress = ProgressDialog(self.root, "Processing...")
        
        def run_operation():
            try:
                result = operation()
                # FIX: Capture result properly
                self.root.after(0, lambda r=result: self.handle_async_success(progress, r, success_callback))
            except Exception as error:
                # FIX: Capture error properly
                self.root.after(0, lambda e=error: self.handle_async_error(progress, e, error_callback))
        
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
        wizard.geometry("550x500")  # Increased size
        wizard.transient(self.root)
        wizard.grab_set()
        
        # Form fields
        fields = {}
        
        tk.Label(wizard, text="Create New GitHub Account", 
                font=('Arial', 14, 'bold')).pack(pady=15)
        
        form_frame = tk.Frame(wizard)
        form_frame.pack(pady=20, padx=30, fill='both')
        
        # Account name
        tk.Label(form_frame, text="Account Name:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=10)
        fields['name'] = tk.Entry(form_frame, width=35, font=('Arial', 9))
        fields['name'].grid(row=0, column=1, pady=10, padx=15, sticky='w')
        
        # Email
        tk.Label(form_frame, text="Email:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=10)
        fields['email'] = tk.Entry(form_frame, width=35, font=('Arial', 9))
        fields['email'].grid(row=1, column=1, pady=10, padx=15, sticky='w')
        
        # GitHub username
        tk.Label(form_frame, text="GitHub Username:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=10)
        fields['github_username'] = tk.Entry(form_frame, width=35, font=('Arial', 9))
        fields['github_username'].grid(row=2, column=1, pady=10, padx=15, sticky='w')
        
        # GitHub token (optional)
        tk.Label(form_frame, text="GitHub Token (Optional):", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=10)
        fields['token'] = tk.Entry(form_frame, width=35, show="*", font=('Arial', 9))
        fields['token'].grid(row=3, column=1, pady=10, padx=15, sticky='w')
        
        # Help text
        help_text = "💡 Adding a token enables automatic repository creation\nGenerate at: GitHub.com → Settings → Developer settings → Personal access tokens"
        tk.Label(form_frame, text=help_text, font=('Arial', 8), fg='gray', justify='left').grid(
            row=4, column=0, columnspan=2, sticky='w', pady=15)
        
        # Buttons
        button_frame = tk.Frame(wizard)
        button_frame.pack(pady=25, fill='x', padx=30)
        
        def create_account():
            # Validate inputs
            name = fields['name'].get().strip()
            email = fields['email'].get().strip()
            github_username = fields['github_username'].get().strip()
            token = fields['token'].get().strip()
            
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
            self.create_account_with_ssh_key(name, email, github_username, token)
        
        tk.Button(button_frame, text="Create Account", 
                 command=create_account, font=('Arial', 10, 'bold'),
                 bg='#28a745', fg='white', width=15).pack(side='right', padx=5)
        tk.Button(button_frame, text="Cancel", 
                 command=wizard.destroy, font=('Arial', 10), width=10).pack(side='right', padx=5)
        
        # Focus on first field
        fields['name'].focus()
    
    def create_account_with_ssh_key(self, name: str, email: str, github_username: str, token: str = ""):
        """Create account and generate SSH key - FIXED VERSION"""
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
                github_username=github_username,
                token=token if token else None
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
                # FIX: Capture the result variable properly
                self.root.after(0, lambda r=result: [progress.close(), on_success(r)])
            except Exception as error:
                # FIX: Capture the error variable properly using default parameter
                self.root.after(0, lambda e=error: [progress.close(), on_error(e)])
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
    
    def show_ssh_key_instructions(self, account: Account):
        """Show instructions for adding SSH key to GitHub"""
        instructions = tk.Toplevel(self.root)
        instructions.title("Add SSH Key to GitHub")
        instructions.geometry("600x500")  # Increased size
        instructions.transient(self.root)
        
        tk.Label(instructions, text="SSH Key Generated Successfully!", 
                font=('Arial', 14, 'bold'), fg='green').pack(pady=15)
        
        text_frame = tk.Frame(instructions)
        text_frame.pack(pady=15, padx=25, fill='both', expand=True)
        
        text = f"""Your SSH key has been generated and added to SSH agent.

Next steps:
1. Copy the public key below
2. Go to GitHub.com → Settings → SSH and GPG keys
3. Click "New SSH key"
4. Paste the key and save

Public Key for {account.name}:"""
        
        tk.Label(text_frame, text=text, justify='left', font=('Arial', 10)).pack(anchor='w')
        
        # Public key text area
        key_text = tk.Text(text_frame, height=10, width=70, font=('Consolas', 9))
        key_text.pack(pady=15, fill='both', expand=True)
        
        try:
            with open(f"{account.ssh_key_path}.pub", 'r') as f:
                public_key = f.read()
                key_text.insert('1.0', public_key)
                key_text.config(state='disabled')
        except Exception as e:
            key_text.insert('1.0', f"Error reading public key: {e}")
        
        # Buttons
        button_frame = tk.Frame(instructions)
        button_frame.pack(pady=20, fill='x', padx=25)
        
        def copy_key():
            self.root.clipboard_clear()
            self.root.clipboard_append(public_key)
            self.show_success("Public key copied to clipboard!")
        
        tk.Button(button_frame, text="Copy Key", command=copy_key, 
                 font=('Arial', 10), width=12).pack(side='left', padx=5)
        tk.Button(button_frame, text="Open GitHub", 
                 command=lambda: webbrowser.open("https://github.com/settings/keys"),
                 font=('Arial', 10), width=12).pack(side='left', padx=5)
        tk.Button(button_frame, text="Done", command=instructions.destroy, 
                 font=('Arial', 10, 'bold'), width=10).pack(side='right', padx=5)
    
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
        columns = ('Name', 'Email', 'GitHub Username', 'Token Status', 'SSH Key')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            if col == 'Token Status':
                self.accounts_tree.column(col, width=120)
            else:
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
        
        # Status label
        self.scan_status_label = ttk.Label(scan_frame, text="Click 'Scan' to find repositories", 
                                          font=('Arial', 9), foreground='gray')
        self.scan_status_label.pack(pady=2)
        
        # Repositories list
        repos_list_frame = ttk.LabelFrame(self.repos_frame, text="Repositories")
        repos_list_frame.pack(fill='both', expand=True, pady=10, padx=10)
        
        # Configure grid weights
        repos_list_frame.grid_rowconfigure(0, weight=1)
        repos_list_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for repositories
        repo_columns = ('Repository', 'Account Status', 'Remote URL', 'Git Status')
        self.repos_tree = ttk.Treeview(repos_list_frame, columns=repo_columns, show='headings')
        
        # Configure column widths and headings
        self.repos_tree.heading('Repository', text='📁 Repository')
        self.repos_tree.column('Repository', width=200, minwidth=150)
        
        self.repos_tree.heading('Account Status', text='👤 Account Status')
        self.repos_tree.column('Account Status', width=200, minwidth=150)
        
        self.repos_tree.heading('Remote URL', text='🔗 Remote URL')
        self.repos_tree.column('Remote URL', width=250, minwidth=200)
        
        self.repos_tree.heading('Git Status', text='📊 Git Status')
        self.repos_tree.column('Git Status', width=200, minwidth=150)
        
        # Add scrollbars
        h_scrollbar = ttk.Scrollbar(repos_list_frame, orient="horizontal", command=self.repos_tree.xview)
        v_scrollbar = ttk.Scrollbar(repos_list_frame, orient="vertical", command=self.repos_tree.yview)
        self.repos_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.repos_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Repository actions
        actions_frame = ttk.Frame(repos_list_frame)
        actions_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Button(actions_frame, text="🔗 Set Up Remote & Account", 
                  command=self.configure_new_repo).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="🔄 Change Repository Account", 
                  command=self.switch_repo_account).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="🧹 Reset Repository Config", 
                  command=self.reset_repo_config).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="🔍 Show Repository Details", 
                  command=self.show_repo_details).pack(side='left', padx=5)
    
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
            token_status = "✅ Has Token" if account.token else "⚠️ No Token"
            self.accounts_tree.insert('', 'end', values=(
                account.name,
                account.email,
                account.github_username or 'Not set',
                token_status,
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
        
        # Create edit dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Account: {account_name}")
        edit_window.geometry("600x550")  # Increased size
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Header
        tk.Label(edit_window, text=f"Edit Account: {account_name}", 
                font=('Arial', 14, 'bold')).pack(pady=15)
        
        # Form frame
        form_frame = tk.LabelFrame(edit_window, text="Account Details", font=('Arial', 10, 'bold'))
        form_frame.pack(fill='x', padx=25, pady=15)
        
        # Email
        tk.Label(form_frame, text="Email:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=15, padx=15)
        email_var = tk.StringVar(value=account.email)
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=40, font=('Arial', 9))
        email_entry.grid(row=0, column=1, pady=15, padx=15, sticky='w')
        
        # GitHub username
        tk.Label(form_frame, text="GitHub Username:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=15, padx=15)
        username_var = tk.StringVar(value=account.github_username or "")
        username_entry = tk.Entry(form_frame, textvariable=username_var, width=40, font=('Arial', 9))
        username_entry.grid(row=1, column=1, pady=15, padx=15, sticky='w')
        
        # GitHub token
        tk.Label(form_frame, text="GitHub Token:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=15, padx=15)
        token_var = tk.StringVar(value=account.token or "")
        token_entry = tk.Entry(form_frame, textvariable=token_var, width=40, show="*", font=('Arial', 9))
        token_entry.grid(row=2, column=1, pady=15, padx=15, sticky='w')
        
        # Show/hide token button
        show_token_var = tk.BooleanVar()
        def toggle_token_visibility():
            if show_token_var.get():
                token_entry.config(show="")
            else:
                token_entry.config(show="*")
        
        tk.Checkbutton(form_frame, text="Show token", variable=show_token_var, 
                      command=toggle_token_visibility).grid(row=3, column=1, sticky='w', padx=15, pady=5)
        
        # Help text
        help_frame = tk.Frame(edit_window)
        help_frame.pack(fill='x', padx=25, pady=15)
        
        help_text = """💡 Tips:
• Token enables automatic repository creation on GitHub
• Generate new tokens at: GitHub.com → Settings → Developer settings → Personal access tokens
• Required scopes: 'repo' (for repository access)
• SSH key path cannot be changed here"""
        
        tk.Label(help_frame, text=help_text, font=('Arial', 8), fg='gray', justify='left').pack(anchor='w')
        
        # SSH key info
        ssh_frame = tk.LabelFrame(edit_window, text="SSH Key Information", font=('Arial', 10, 'bold'))
        ssh_frame.pack(fill='x', padx=25, pady=15)
        
        tk.Label(ssh_frame, text=f"SSH Key Path: {account.ssh_key_path}", 
                font=('Arial', 9)).pack(anchor='w', padx=15, pady=10)
        
        def open_ssh_key():
            try:
                # Open SSH key file in default text editor
                if platform.system() == "Windows":
                    os.startfile(f"{account.ssh_key_path}.pub")
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", f"{account.ssh_key_path}.pub"])
                else:  # Linux
                    subprocess.run(["xdg-open", f"{account.ssh_key_path}.pub"])
            except Exception as e:
                self.show_error(f"Could not open SSH key file: {e}")
        
        tk.Button(ssh_frame, text="📄 View Public Key", command=open_ssh_key, 
                 font=('Arial', 9)).pack(anchor='w', padx=15, pady=10)
        
        # Buttons
        button_frame = tk.Frame(edit_window)
        button_frame.pack(fill='x', padx=25, pady=25)
        
        def save_changes():
            # Validate inputs
            email = email_var.get().strip()
            username = username_var.get().strip()
            token = token_var.get().strip()
            
            if not email or not username:
                self.show_error("Email and GitHub username are required")
                return
            
            if not self.validate_inputs(email=email, github_username=username):
                return
            
            # Update account
            account.email = email
            account.github_username = username
            account.token = token if token else None
            
            # Save configuration
            self.save_config()
            self.refresh_accounts_list()
            
            self.show_success(f"Account '{account_name}' updated successfully!")
            edit_window.destroy()
        
        def test_token():
            """Test if the GitHub token is valid"""
            token = token_var.get().strip()
            if not token:
                self.show_error("Please enter a token to test")
                return
            
            def test_token_async():
                try:
                    import requests
                    headers = {"Authorization": f"token {token}"}
                    response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        user_data = response.json()
                        return True, f"Token valid! Authenticated as: {user_data.get('login', 'Unknown')}"
                    else:
                        return False, f"Token invalid. Status: {response.status_code}"
                except Exception as e:
                    return False, f"Test failed: {str(e)}"
            
            def on_test_complete(result):
                success, message = result
                if success:
                    self.show_success(message)
                else:
                    self.show_error(message)
            
            self.safe_async_operation(test_token_async, on_test_complete, progress_title="Testing Token...")
        
        # Button layout
        tk.Button(button_frame, text="🧪 Test Token", command=test_token, 
                 font=('Arial', 10), width=12).pack(side='left')
        tk.Button(button_frame, text="Cancel", command=edit_window.destroy, 
                 font=('Arial', 10), width=10).pack(side='right', padx=(5, 0))
        tk.Button(button_frame, text="💾 Save Changes", command=save_changes, 
                 bg='#28a745', fg='white', font=('Arial', 10, 'bold'), width=15).pack(side='right')
        
        # Focus on email field
        email_entry.focus()
    
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
        """Test SSH connection for selected account - FIXED VERSION"""
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
        
        self.safe_async_operation(test_connection, on_test_complete, progress_title="Testing SSH Connection...")
    
    def browse_folder(self):
        """Browse for folder to scan"""
        folder = filedialog.askdirectory(initialdir=self.last_scanned_path)
        if folder:
            self.path_var.set(folder)
            self.last_scanned_path = folder
            self.save_config()
    
    def scan_repositories(self):
        """Scan for repositories in the selected path - FIXED VERSION"""
        path = self.path_var.get()
        if not path or not os.path.isdir(path):
            self.show_error("Please select a valid directory to scan")
            return
        
        # Update status
        self.scan_status_label.config(text="🔍 Scanning for repositories...", foreground='blue')
        self.root.update()
        
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
                        repos.append((root, f'❌ Error', f'Error: {e}', 'Error reading repository'))
            return repos
        
        def on_scan_complete(repos):
            self.repos = repos
            self.refresh_repos_list()
            
            # Update status with results
            if repos:
                self.scan_status_label.config(
                    text=f"✅ Found {len(repos)} repositories in {os.path.basename(path)}", 
                    foreground='green'
                )
            else:
                self.scan_status_label.config(
                    text=f"❌ No Git repositories found in {os.path.basename(path)}", 
                    foreground='orange'
                )
        
        def on_scan_error(error):
            self.scan_status_label.config(
                text=f"❌ Scan failed: {str(error)[:50]}", 
                foreground='red'
            )
        
        self.safe_async_operation(scan, on_scan_complete, on_scan_error, "Scanning Repositories...")
    def get_repo_status(self, repo) -> str:
        """Get repository status"""
        try:
            status_parts = []
            
            # Check working directory status
            if repo.is_dirty():
                status_parts.append("📝 Modified")
            
            if repo.untracked_files:
                untracked_count = len(repo.untracked_files)
                status_parts.append(f"📄 {untracked_count} Untracked")
            
            # Check if there are commits
            try:
                repo.head.commit
                has_commits = True
            except:
                has_commits = False
                status_parts.append("🆕 No Commits")
            
            # Check remote tracking
            if has_commits:
                try:
                    if 'origin' in repo.remotes:
                        # Check if local branch tracks remote
                        try:
                            tracking_branch = repo.active_branch.tracking_branch()
                            if tracking_branch:
                                # Check if ahead/behind
                                ahead_behind = list(repo.iter_commits(f'{tracking_branch}..HEAD'))
                                behind_ahead = list(repo.iter_commits(f'HEAD..{tracking_branch}'))
                                
                                if ahead_behind:
                                    status_parts.append(f"⬆️ {len(ahead_behind)} Ahead")
                                if behind_ahead:
                                    status_parts.append(f"⬇️ {len(behind_ahead)} Behind")
                            else:
                                status_parts.append("🔗 Not Tracking Remote")
                        except:
                            status_parts.append("🔗 No Remote Branch")
                    else:
                        status_parts.append("📡 No Remote")
                except:
                    pass
            
            if not status_parts:
                status_parts.append("✅ Clean")
            
            return " | ".join(status_parts)
        except Exception as e:
            return f"❌ Error: {str(e)[:30]}"
    
    def detect_repo_account(self, remote_url: str) -> str:
        """Detect which account a repository belongs to"""
        if not remote_url or remote_url == 'No remote':
            return '🆕 No Remote (Ready to Configure)'
        
        # Check for SSH URLs with account host
        match = re.match(r'git@github\.com-(\w+):', remote_url)
        if match:
            account_name = match.group(1)
            if account_name in self.accounts:
                return f'✅ {account_name}'
            else:
                return f'❓ Unknown Account ({account_name})'
        
        # Check for standard SSH URLs
        if remote_url.startswith('git@github.com:'):
            return '🔄 GitHub SSH (Needs Account Assignment)'
        
        # Check for HTTPS URLs
        if 'github.com' in remote_url:
            return '🔗 GitHub HTTPS (Convert to SSH)'
        
        return '🚫 Non-GitHub Repository'
    
    def refresh_repos_list(self):
        """Refresh the repositories list"""
        # Clear existing items
        for item in self.repos_tree.get_children():
            self.repos_tree.delete(item)
        
        # Add repositories
        for repo_data in self.repos:
            path, account, remote_url, status = repo_data
            
            # Create display name (relative to scanned path or just folder name)
            if self.path_var.get() and path.startswith(self.path_var.get()):
                display_path = path.replace(self.path_var.get(), '').lstrip(os.sep) or os.path.basename(path)
            else:
                display_path = os.path.basename(path)
            
            # Truncate remote URL for display
            display_remote = remote_url
            if len(remote_url) > 50:
                display_remote = remote_url[:47] + '...'
            
            # Insert row with improved formatting
            self.repos_tree.insert('', 'end', values=(
                display_path,
                account,
                display_remote,
                status
            ))
        
        # Update status
        count = len(self.repos)
        if hasattr(self, 'scan_status_label'):
            if count > 0:
                self.scan_status_label.config(
                    text=f"✅ Displaying {count} repositories", 
                    foreground='green'
                )
            else:
                self.scan_status_label.config(
                    text="No repositories found", 
                    foreground='orange'
                )
    
    # Repository management methods
    def configure_new_repo(self):
        """Set up remote and account for a new repository"""
        selection = self.repos_tree.selection()
        if not selection:
            self.show_error("Please select a repository to configure")
            return
        
        # Get repository data
        item = selection[0]
        repo_index = self.repos_tree.index(item)
        repo_path, current_account, remote_url, status = self.repos[repo_index]
        
        # Check if repo already has a remote
        if remote_url != 'No remote':
            result = messagebox.askyesno(
                "Repository Has Remote",
                f"This repository already has a remote:\n{remote_url}\n\n"
                "Do you want to replace it with a new configuration?"
            )
            if not result:
                return
        
        # Show configuration dialog
        self.show_repo_config_dialog(repo_path, "Set Up Repository")
    
    def switch_repo_account(self):
        """Change the account for an existing repository"""
        selection = self.repos_tree.selection()
        if not selection:
            self.show_error("Please select a repository to switch accounts")
            return
        
        # Get repository data
        item = selection[0]
        repo_index = self.repos_tree.index(item)
        repo_path, current_account, remote_url, status = self.repos[repo_index]
        
        # Check if repo has a remote
        if remote_url == 'No remote':
            self.show_error("This repository has no remote. Use 'Set Up Remote & Account' instead.")
            return
        
        if 'Error' in current_account or 'Non-GitHub' in current_account:
            self.show_error("Cannot switch accounts for non-GitHub repositories")
            return
        
        # Show account switching dialog
        self.show_account_switch_dialog(repo_path, current_account, remote_url)
    
    def reset_repo_config(self):
        """Reset repository configuration and start fresh"""
        selection = self.repos_tree.selection()
        if not selection:
            self.show_error("Please select a repository to reset")
            return
        
        # Get repository data
        item = selection[0]
        repo_index = self.repos_tree.index(item)
        repo_path, current_account, remote_url, status = self.repos[repo_index]
        
        # Confirm reset
        result = messagebox.askyesno(
            "Reset Repository Configuration",
            f"This will:\n"
            f"• Remove the current remote: {remote_url}\n"
            f"• Clear Git user configuration\n"
            f"• Allow you to set up fresh configuration\n\n"
            f"Repository files will NOT be affected.\n\n"
            f"Continue?"
        )
        
        if not result:
            return
        
        try:
            repo = Repo(repo_path)
            
            # Remove remote if it exists
            if 'origin' in repo.remotes:
                repo.delete_remote('origin')
            
            # Clear Git user config for this repository
            with repo.config_writer() as config:
                try:
                    config.remove_option("user", "name")
                    config.remove_option("user", "email")
                except:
                    pass  # Config might not exist
            
            self.show_success("Repository configuration reset successfully!")
            self.scan_repositories()  # Refresh the list
            
        except Exception as e:
            self.show_error(f"Failed to reset repository configuration: {e}")
    
    def show_repo_details(self):
        """Show detailed information about the selected repository"""
        selection = self.repos_tree.selection()
        if not selection:
            self.show_error("Please select a repository to view details")
            return
        
        # Get repository data
        item = selection[0]
        repo_index = self.repos_tree.index(item)
        repo_path, current_account, remote_url, status = self.repos[repo_index]
        
        # Get detailed repo info
        try:
            repo = Repo(repo_path)
            
            # Get Git config
            try:
                config_name = repo.config_reader().get_value("user", "name", "Not set")
                config_email = repo.config_reader().get_value("user", "email", "Not set")
            except:
                config_name = config_email = "Not set"
            
            # Get branch info
            try:
                current_branch = repo.active_branch.name
                branches = [branch.name for branch in repo.branches]
            except:
                current_branch = "Unknown"
                branches = []
            
            # Get last commit info
            try:
                last_commit = repo.head.commit
                commit_info = f"{last_commit.author.name} - {last_commit.message.strip()[:50]}..."
                commit_date = last_commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
            except:
                commit_info = "No commits"
                commit_date = "N/A"
            
            # Show details dialog
            self.show_repo_details_dialog(repo_path, {
                'current_account': current_account,
                'remote_url': remote_url,
                'status': status,
                'config_name': config_name,
                'config_email': config_email,
                'current_branch': current_branch,
                'branches': branches,
                'commit_info': commit_info,
                'commit_date': commit_date
            })
            
        except Exception as e:
            self.show_error(f"Failed to get repository details: {e}")
    
    def show_repo_config_dialog(self, repo_path: str, title: str):
        """Show repository configuration dialog - FIXED VERSION"""
        if not self.accounts:
            self.show_error("No accounts configured. Please add an account first.")
            return
        
        # Create and configure the dialog window
        config_window = tk.Toplevel(self.root)
        config_window.title(title)
        config_window.geometry("700x750")  # Increased size further
        config_window.transient(self.root)
        config_window.grab_set()
        config_window.resizable(True, True)
        
        # Ensure window appears properly
        config_window.update_idletasks()
        config_window.lift()
        config_window.focus_force()
        
        # Create a canvas and scrollbar for scrolling
        canvas = tk.Canvas(config_window)
        scrollbar = ttk.Scrollbar(config_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Main container
        main_frame = tk.Frame(scrollable_frame)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text=title, 
                font=('Arial', 16, 'bold')).pack()
        tk.Label(header_frame, text=f"Repository: {os.path.basename(repo_path)}", 
                font=('Arial', 10)).pack(pady=5)
        
        # Form frame with better organization
        form_frame = tk.LabelFrame(main_frame, text="Repository Configuration", 
                                  font=('Arial', 10, 'bold'))
        form_frame.pack(fill='x', pady=(0, 20), padx=10, ipady=15)
        
        # Account selection
        account_frame = tk.Frame(form_frame)
        account_frame.pack(fill='x', padx=15, pady=15)
        
        tk.Label(account_frame, text="Select Account:", 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        account_var = tk.StringVar()
        account_combo = ttk.Combobox(account_frame, textvariable=account_var, 
                                   values=list(self.accounts.keys()), 
                                   state='readonly', width=40, font=('Arial', 9))
        account_combo.pack(anchor='w', pady=(0, 15))
        
        if self.accounts:
            account_combo.set(list(self.accounts.keys())[0])  # Select first account
        
        # Repository details
        repo_details_frame = tk.Frame(form_frame)
        repo_details_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(repo_details_frame, text="GitHub Owner/Username:", 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        owner_var = tk.StringVar()
        owner_entry = tk.Entry(repo_details_frame, textvariable=owner_var, width=40, font=('Arial', 9))
        owner_entry.pack(anchor='w', pady=(0, 15))
        
        tk.Label(repo_details_frame, text="Repository Name:", 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        repo_name_var = tk.StringVar(value=os.path.basename(repo_path))
        repo_name_entry = tk.Entry(repo_details_frame, textvariable=repo_name_var, width=40, font=('Arial', 9))
        repo_name_entry.pack(anchor='w', pady=(0, 10))
        
        # Auto-fill owner from selected account
        def update_owner(*args):
            selected_account = account_var.get()
            if selected_account and selected_account in self.accounts:
                account = self.accounts[selected_account]
                if account.github_username:
                    owner_var.set(account.github_username)
        
        account_var.trace('w', update_owner)
        update_owner()  # Initial update
        
        # Options section
        options_frame = tk.LabelFrame(main_frame, text="GitHub Repository Options", 
                                    font=('Arial', 10, 'bold'))
        options_frame.pack(fill='x', pady=(0, 20), padx=10, ipady=15)
        
        options_inner = tk.Frame(options_frame)
        options_inner.pack(fill='x', padx=15, pady=15)
        
        create_repo_var = tk.BooleanVar()
        tk.Checkbutton(options_inner, text="Create repository on GitHub automatically", 
                      variable=create_repo_var, font=('Arial', 9)).pack(anchor='w', pady=2)
        
        private_repo_var = tk.BooleanVar()
        tk.Checkbutton(options_inner, text="Make repository private", 
                      variable=private_repo_var, font=('Arial', 9)).pack(anchor='w', pady=2)
        
        # GitHub token section
        token_frame = tk.LabelFrame(main_frame, text="GitHub Token", 
                                  font=('Arial', 10, 'bold'))
        token_frame.pack(fill='x', pady=(0, 20), padx=10, ipady=15)
        
        token_inner = tk.Frame(token_frame)
        token_inner.pack(fill='x', padx=15, pady=15)
        
        # Token info and override
        token_status_var = tk.StringVar()
        token_status_label = tk.Label(token_inner, textvariable=token_status_var, 
                                    font=('Arial', 9), fg='gray')
        token_status_label.pack(anchor='w', pady=(0, 10))
        
        tk.Label(token_inner, text="Override Token (Optional):", 
                font=('Arial', 9)).pack(anchor='w', pady=(0, 5))
        token_var = tk.StringVar()
        token_entry = tk.Entry(token_inner, textvariable=token_var, show="*", width=50, font=('Arial', 9))
        token_entry.pack(anchor='w', pady=(0, 10))
        
        tk.Label(token_inner, text="💡 Leave empty to use account token. Generate at: GitHub.com → Settings → Developer settings → Personal access tokens", 
                font=('Arial', 8), fg='gray').pack(anchor='w')
        
        def update_token_status(*args):
            """Update token status based on selected account"""
            selected_account = account_var.get()
            if selected_account and selected_account in self.accounts:
                account = self.accounts[selected_account]
                if account.token:
                    token_status_var.set("✅ Account has token - automatic repo creation available")
                    token_status_label.config(fg='green')
                else:
                    token_status_var.set("⚠️ No token stored for this account - manual repo creation only")
                    token_status_label.config(fg='orange')
            else:
                token_status_var.set("")
        
        account_var.trace('w', update_token_status)
        update_token_status()  # Initial update
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame - Always visible at bottom of window (not in scrollable area)
        button_frame = tk.Frame(config_window, bg='lightgray', relief='raised', bd=1)
        button_frame.pack(side='bottom', fill='x', padx=0, pady=0)
        
        # Inner button frame for padding
        button_inner = tk.Frame(button_frame, bg='lightgray')
        button_inner.pack(fill='x', padx=20, pady=15)
        
        def configure_repository():
            """Handle repository configuration"""
            account_name = account_var.get()
            owner = owner_var.get().strip()
            repo_name = repo_name_var.get().strip()
            create_repo = create_repo_var.get()
            private_repo = private_repo_var.get()
            override_token = token_var.get().strip()
            
            # Validate inputs
            if not account_name or not owner or not repo_name:
                self.show_error("Please fill in all required fields")
                return
            
            # Validate account exists
            if account_name not in self.accounts:
                self.show_error(f"Account '{account_name}' not found")
                return
            
            # Determine which token to use
            account = self.accounts[account_name]
            token_to_use = override_token if override_token else account.token
            
            # Check token requirement for auto-creation
            if create_repo and not token_to_use:
                result = messagebox.askyesno("No Token Available", 
                                           f"No GitHub token available for account '{account_name}'.\n\n"
                                           "Repository will need to be created manually on GitHub.\n\n"
                                           "Continue with local configuration only?\n\n"
                                           "Tip: Add a token to the account in the Accounts tab for automatic creation.")
                if not result:
                    return
                create_repo = False
            
            # Close dialog and proceed
            config_window.destroy()
            self.apply_repo_configuration(repo_path, account_name, owner, repo_name, create_repo, private_repo, token_to_use)
        
        def cancel_configuration():
            """Handle dialog cancellation"""
            config_window.destroy()
        
        # Button layout - Now always visible at bottom
        cancel_btn = tk.Button(button_inner, text="Cancel", 
                             command=cancel_configuration, 
                             font=('Arial', 10), width=12)
        cancel_btn.pack(side='right', padx=(10, 0))
        
        configure_btn = tk.Button(button_inner, text="✅ Configure Repository", 
                                command=configure_repository, 
                                bg='#28a745', fg='white', 
                                font=('Arial', 10, 'bold'), width=20)
        configure_btn.pack(side='right')
        
        # Bind mouse wheel to canvas for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Focus and final setup
        owner_entry.focus()
        config_window.protocol("WM_DELETE_WINDOW", cancel_configuration)
        
        # Ensure dialog is properly displayed
        config_window.update()
        config_window.deiconify()
        
        print(f"Repository config dialog created for: {repo_path}")
    
    def show_account_switch_dialog(self, repo_path: str, current_account: str, current_remote: str):
        """Show dialog to switch repository account"""
        if not self.accounts:
            self.show_error("No accounts configured. Please add an account first.")
            return
        
        switch_window = tk.Toplevel(self.root)
        switch_window.title("Change Repository Account")
        switch_window.geometry("550x400")  # Increased size
        switch_window.transient(self.root)
        switch_window.grab_set()
        
        # Header
        tk.Label(switch_window, text="Change Repository Account", 
                font=('Arial', 16, 'bold')).pack(pady=15)
        
        # Current info
        info_frame = tk.LabelFrame(switch_window, text="Current Configuration")
        info_frame.pack(pady=15, padx=25, fill='x')
        
        repo_name = os.path.basename(repo_path)
        tk.Label(info_frame, text=f"Repository: {repo_name}", 
                font=('Arial', 10)).pack(anchor='w', padx=15, pady=8)
        tk.Label(info_frame, text=f"Current Account: {current_account}", 
                font=('Arial', 10)).pack(anchor='w', padx=15, pady=8)
        
        # Truncate remote URL if too long
        display_remote = current_remote
        if len(current_remote) > 60:
            display_remote = current_remote[:60] + '...'
        tk.Label(info_frame, text=f"Remote URL: {display_remote}", 
                font=('Arial', 10)).pack(anchor='w', padx=15, pady=8)
        
        # New account selection
        selection_frame = tk.LabelFrame(switch_window, text="New Configuration")
        selection_frame.pack(pady=15, padx=25, fill='x')
        
        tk.Label(selection_frame, text="Switch to Account:", 
                font=('Arial', 10, 'bold')).pack(anchor='w', padx=15, pady=10)
        
        account_var = tk.StringVar()
        available_accounts = []
        for acc in self.accounts.keys():
            if acc != current_account:
                available_accounts.append(acc)
        
        if not available_accounts:
            tk.Label(selection_frame, text="No other accounts available", 
                    fg='red').pack(anchor='w', padx=15, pady=10)
            tk.Button(switch_window, text="Close", 
                     command=switch_window.destroy, font=('Arial', 10), width=10).pack(pady=20)
            return
        
        account_combo = ttk.Combobox(selection_frame, textvariable=account_var, 
                                   values=available_accounts, state='readonly', width=30, font=('Arial', 9))
        account_combo.pack(anchor='w', padx=15, pady=5)
        account_combo.set(available_accounts[0])
        
        # Preview new URL
        preview_frame = tk.Frame(selection_frame)
        preview_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(preview_frame, text="New Remote URL:", 
                font=('Arial', 9)).pack(anchor='w')
        preview_label = tk.Label(preview_frame, text="", 
                               font=('Arial', 9), fg='blue')
        preview_label.pack(anchor='w')
        
        def update_preview(*args):
            selected_account = account_var.get()
            if selected_account:
                # Extract repo info from current URL
                repo_info = self.extract_repo_info_from_url(current_remote)
                if repo_info:
                    new_url = f"git@github.com-{selected_account}:{repo_info['owner']}/{repo_info['repo']}.git"
                    preview_label.config(text=new_url)
                else:
                    preview_label.config(text="Unable to parse repository info")
        
        account_var.trace('w', update_preview)
        update_preview()  # Initial update
        
        # Buttons
        button_frame = tk.Frame(switch_window)
        button_frame.pack(pady=25, fill='x', padx=25)
        
        def switch_account():
            new_account = account_var.get()
            if not new_account:
                self.show_error("Please select an account")
                return
            
            switch_window.destroy()
            self.apply_account_switch(repo_path, current_account, new_account, current_remote)
        
        tk.Button(button_frame, text="Cancel", 
                 command=switch_window.destroy, font=('Arial', 10), width=10).pack(side='right', padx=5)
        tk.Button(button_frame, text="🔄 Switch Account", 
                 command=switch_account, bg='#007bff', fg='white', 
                 font=('Arial', 10, 'bold'), width=15).pack(side='right')
    
    def extract_repo_info_from_url(self, url: str) -> Optional[Dict]:
        """Extract owner and repo name from Git URL"""
        if not url:
            return None
        
        # SSH URL patterns
        ssh_patterns = [
            r'git@github\.com[:-](.+?):(.+?)/(.+?)(?:\.git)?$',  # with account host
            r'git@github\.com:(.+?)/(.+?)(?:\.git)?$'            # standard
        ]
        
        # HTTPS URL pattern
        https_pattern = r'https://github\.com/(.+?)/(.+?)(?:\.git)?/?$'
        
        for pattern in ssh_patterns:
            match = re.match(pattern, url)
            if match:
                if len(match.groups()) == 3:  # Account host format
                    return {
                        "host": match.group(1),
                        "owner": match.group(2),
                        "repo": match.group(3),
                        "protocol": "ssh"
                    }
                else:  # Standard format
                    return {
                        "host": None,
                        "owner": match.group(1),
                        "repo": match.group(2),
                        "protocol": "ssh"
                    }
        
        # Try HTTPS pattern
        match = re.match(https_pattern, url)
        if match:
            return {
                "host": None,
                "owner": match.group(1),
                "repo": match.group(2),
                "protocol": "https"
            }
        
        return None
    
    def apply_repo_configuration(self, repo_path: str, account_name: str, owner: str, 
                                repo_name: str, create_repo: bool, private_repo: bool, token: str):
        """Apply repository configuration"""
        try:
            repo = Repo(repo_path)
            account = self.accounts[account_name]
            
            # Create remote URL
            remote_url = f"git@github.com-{account_name}:{owner}/{repo_name}.git"
            
            # Remove existing remote if it exists
            if 'origin' in repo.remotes:
                repo.delete_remote('origin')
            
            # Add new remote
            repo.create_remote('origin', remote_url)
            
            # Configure Git user for this repository
            with repo.config_writer() as config:
                config.set_value("user", "name", account.name)
                config.set_value("user", "email", account.email)
            
            # Create GitHub repository if requested
            if create_repo and token:
                success, message = self.create_github_repository(owner, repo_name, token, private_repo)
                if not success:
                    self.show_error(f"Repository configured locally but GitHub creation failed:\n{message}")
                else:
                    self.show_success(f"Repository configured and created on GitHub successfully!\n\n"
                                    f"Remote URL: {remote_url}\n"
                                    f"Account: {account_name}\n\n"
                                    f"You can now push your code:\n"
                                    f"git add .\n"
                                    f"git commit -m 'Initial commit'\n"
                                    f"git push -u origin main")
            else:
                self.show_success(f"Repository configured successfully!\n\n"
                                f"Remote URL: {remote_url}\n"
                                f"Account: {account_name}\n\n"
                                f"Create the repository on GitHub, then push:\n"
                                f"git add .\n"
                                f"git commit -m 'Initial commit'\n"
                                f"git push -u origin main")
            
            # Refresh repository list
            self.scan_repositories()
            
        except Exception as e:
            self.show_error(f"Failed to configure repository: {e}")
    
    def apply_account_switch(self, repo_path: str, old_account: str, new_account: str, old_remote: str):
        """Apply account switch to repository"""
        try:
            repo = Repo(repo_path)
            new_account_obj = self.accounts[new_account]
            
            # Extract repository info from old URL
            repo_info = self.extract_repo_info_from_url(old_remote)
            if not repo_info:
                self.show_error("Could not parse repository information from remote URL")
                return
            
            # Create new remote URL
            new_remote_url = f"git@github.com-{new_account}:{repo_info['owner']}/{repo_info['repo']}.git"
            
            # Update remote URL
            repo.remotes.origin.set_url(new_remote_url)
            
            # Update Git user configuration
            with repo.config_writer() as config:
                config.set_value("user", "name", new_account_obj.name)
                config.set_value("user", "email", new_account_obj.email)
            
            self.show_success(f"Account switched successfully!\n\n"
                            f"Old Account: {old_account}\n"
                            f"New Account: {new_account}\n\n"
                            f"New Remote URL: {new_remote_url}\n\n"
                            f"Future commits will use: {new_account_obj.email}")
            
            # Refresh repository list
            self.scan_repositories()
            
        except Exception as e:
            self.show_error(f"Failed to switch account: {e}")
    
    def create_github_repository(self, owner: str, repo_name: str, token: str, private: bool = False) -> Tuple[bool, str]:
        """Create GitHub repository using API"""
        try:
            url = "https://api.github.com/user/repos"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "name": repo_name,
                "private": private
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                return True, "Repository created successfully"
            elif response.status_code == 422:
                return False, "Repository already exists or invalid name"
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return False, f"GitHub API error: {error_msg}"
        
        except Exception as e:
            return False, f"Network error: {str(e)}"
    
    def show_repo_details_dialog(self, repo_path: str, details: Dict):
        """Show detailed repository information"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Repository Details")
        details_window.geometry("650x500")  # Increased size
        details_window.transient(self.root)
        
        # Header
        tk.Label(details_window, text="Repository Details", 
                font=('Arial', 16, 'bold')).pack(pady=15)
        tk.Label(details_window, text=os.path.basename(repo_path), 
                font=('Arial', 12)).pack(pady=5)
        
        # Details in a scrollable text widget
        text_frame = tk.Frame(details_window)
        text_frame.pack(fill='both', expand=True, padx=25, pady=15)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Format details
        details_text = f"""📁 PATH
{repo_path}

🔗 REMOTE CONFIGURATION
Account: {details['current_account']}
Remote URL: {details['remote_url']}

👤 GIT USER CONFIGURATION
Name: {details['config_name']}
Email: {details['config_email']}

🌿 BRANCH INFORMATION
Current Branch: {details['current_branch']}
All Branches: {', '.join(details['branches']) if details['branches'] else 'None'}

📊 REPOSITORY STATUS
Status: {details['status']}

📝 LAST COMMIT
{details['commit_info']}
Date: {details['commit_date']}

💡 ACTIONS AVAILABLE
• Change Repository Account - Switch to a different GitHub account
• Set Up Remote & Account - Configure remote and account (for new repos)
• Reset Repository Config - Remove all configuration and start fresh
"""
        
        text_widget.insert('1.0', details_text)
        text_widget.config(state='disabled')
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        button_frame = tk.Frame(details_window)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Close", command=details_window.destroy, 
                 font=('Arial', 10, 'bold'), width=10).pack()
    
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