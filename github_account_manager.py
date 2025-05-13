import os
import tkinter as tk
from tkinter import messagebox, filedialog
from git import Repo
from pathlib import Path
import re
import subprocess
import platform
import requests
import json

class GitHubAccountManager:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Account Manager")
        self.ssh_config_path = os.path.expanduser("~/.ssh/config")
        self.ssh_dir = os.path.expanduser("~/.ssh")
        self.configs_dir = os.path.join(os.path.dirname(__file__), "configs")
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        os.makedirs(self.configs_dir, exist_ok=True)
        self.accounts = self.load_ssh_configs()
        self.keys = self.detect_ssh_keys()
        self.repos = []
        self.owner_to_account = {}  # Map GitHub owners to account hosts
        self.account_emails = {}  # Map accounts to their emails

        # Load last scanned path
        self.last_scanned_path = self.load_last_scanned_path()

        # Print and save SSH configs and keys
        self.print_and_save_ssh_configs()

        # GUI Elements
        self.setup_gui()

    def load_last_scanned_path(self):
        """Load the last scanned folder path from config.json."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("last_scanned_path", "")
        except Exception as e:
            print(f"Error loading config: {e}")
        return ""

    def save_last_scanned_path(self, path):
        """Save the last scanned folder path to config.json."""
        try:
            config = {"last_scanned_path": path}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def detect_ssh_keys(self):
        """Detect private SSH keys in ~/.ssh directory."""
        keys = []
        if not os.path.exists(self.ssh_dir):
            return keys
        for file in os.listdir(self.ssh_dir):
            file_path = os.path.join(self.ssh_dir, file)
            if (os.path.isfile(file_path) and
                not file.endswith('.pub') and
                not file.startswith('known_hosts') and
                file not in ['config', 'authorized_keys']):
                keys.append(file_path)
        return keys

    def print_and_save_ssh_configs(self):
        """Print and save SSH config and key information."""
        print("\n=== SSH Private Keys ===")
        if self.keys:
            for key in self.keys:
                print(f"Key: {key}")
        else:
            print("No private keys found in ~/.ssh")

        print("\n=== ~/.ssh/config Contents ===")
        if os.path.exists(self.ssh_config_path):
            with open(self.ssh_config_path, 'r') as f:
                content = f.read()
                print(content)
                # Save to configs folder
                ssh_config_output = os.path.join(self.configs_dir, "ssh_config.txt")
                with open(ssh_config_output, 'w') as f_out:
                    f_out.write(content)
        else:
            print("No ~/.ssh/config file found")
            # Write empty file to indicate no config
            ssh_config_output = os.path.join(self.configs_dir, "ssh_config.txt")
            with open(ssh_config_output, 'w') as f_out:
                f_out.write("")

    def load_ssh_configs(self):
        """Load GitHub SSH configurations from ~/.ssh/config."""
        accounts = {}
        if not os.path.exists(self.ssh_config_path):
            return accounts
        with open(self.ssh_config_path, 'r') as f:
            content = f.read()
            # Match Host blocks for github.com-*
            pattern = r'Host github\.com-(\S+)\s*\n\s*HostName github\.com\s*\n\s*User git\s*\n\s*IdentityFile (\S+)'
            matches = re.findall(pattern, content, re.MULTILINE)
            for host, identity_file in matches:
                accounts[host] = identity_file
        return accounts

    def save_ssh_config(self, host, identity_file):
        """Add or update a SSH configuration in ~/.ssh/config."""
        os.makedirs(os.path.dirname(self.ssh_config_path), exist_ok=True)
        # Read existing config
        if os.path.exists(self.ssh_config_path):
            with open(self.ssh_config_path, 'r') as f:
                content = f.readlines()
        else:
            content = []
        # Remove existing block for this host, if any
        new_content = []
        skip = False
        host_line = f"Host github.com-{host}\n"
        for line in content:
            if line.strip() == host_line.strip():
                skip = True
                continue
            if skip and not line.strip().startswith('Host '):
                continue
            skip = False
            new_content.append(line)
        # Append new config
        config_entry = f"\n# {host} account\nHost github.com-{host}\n    HostName github.com\n    User git\n    IdentityFile {identity_file}\n"
        new_content.append(config_entry)
        with open(self.ssh_config_path, 'w') as f:
            f.writelines(new_content)
        self.accounts[host] = identity_file
        # Update GUI
        self.account_var.set("Select Account")
        self.account_menu['menu'].delete(0, 'end')
        for account in self.accounts.keys():
            self.account_menu['menu'].add_command(label=account, command=tk._setit(self.account_var, account))
        self.update_key_list()
        # Save updated SSH config
        self.print_and_save_ssh_configs()

    def delete_ssh_config(self):
        """Delete a selected SSH configuration from ~/.ssh/config."""
        selected = self.key_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a key configuration")
            return
        key_path = self.key_list.get(selected[0]).split(' -> ')[0]
        host = None
        for h, path in self.accounts.items():
            if path == key_path:
                host = h
                break
        if not host:
            messagebox.showinfo("Info", "Key is not associated with any GitHub account")
            return
        if not messagebox.askyesno("Confirm", f"Delete configuration for github.com-{host}?"):
            return
        # Read and filter out the host block
        with open(self.ssh_config_path, 'r') as f:
            content = f.readlines()
        new_content = []
        skip = False
        host_line = f"Host github.com-{host}\n"
        for line in content:
            if line.strip() == host_line.strip():
                skip = True
                continue
            if skip and not line.strip().startswith('Host '):
                continue
            skip = False
            new_content.append(line)
        with open(self.ssh_config_path, 'w') as f:
            f.writelines(new_content)
        # Remove email mapping
        if host in self.account_emails:
            del self.account_emails[host]
        del self.accounts[host]
        # Update GUI
        self.account_var.set("Select Account")
        self.account_menu['menu'].delete(0, 'end')
        for account in self.accounts.keys():
            self.account_menu['menu'].add_command(label=account, command=tk._setit(self.account_var, account))
        self.update_key_list()
        # Save updated SSH config
        self.print_and_save_ssh_configs()
        messagebox.showinfo("Success", f"Deleted configuration for github.com-{host}")

    def edit_ssh_config(self):
        """Edit the selected SSH configuration."""
        selected = self.key_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a key configuration")
            return
        key_path = self.key_list.get(selected[0]).split(' -> ')[0]
        host = None
        for h, path in self.accounts.items():
            if path == key_path:
                host = h
                break
        if not host:
            messagebox.showinfo("Info", "Key is not associated with any GitHub account")
            return
        # Open a dialog to edit host and key
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit SSH Configuration")
        tk.Label(edit_window, text="Host (e.g., joshua-personal):").grid(row=0, column=0, padx=5, pady=5)
        host_entry = tk.Entry(edit_window, width=20)
        host_entry.grid(row=0, column=1, padx=5, pady=5)
        host_entry.insert(0, host)
        tk.Label(edit_window, text="Identity File:").grid(row=1, column=0, padx=5, pady=5)
        key_var = tk.StringVar(edit_window)
        key_var.set(key_path)
        key_menu = tk.OptionMenu(edit_window, key_var, *self.keys)
        key_menu.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(edit_window, text="Email:").grid(row=2, column=0, padx=5, pady=5)
        email_entry = tk.Entry(edit_window, width=30)
        email_entry.grid(row=2, column=1, padx=5, pady=5)
        email_entry.insert(0, self.account_emails.get(host, ""))
        def save_edit():
            new_host = host_entry.get()
            new_key = key_var.get()
            new_email = email_entry.get().strip()
            if not new_host or not new_key:
                messagebox.showerror("Error", "Please enter both host and identity file")
                return
            if not os.path.exists(new_key):
                messagebox.showerror("Error", "Identity file does not exist")
                return
            if not new_email:
                messagebox.showerror("Error", "Please enter an email")
                return
            # Delete old config
            with open(self.ssh_config_path, 'r') as f:
                content = f.readlines()
            new_content = []
            skip = False
            host_line = f"Host github.com-{host}\n"
            for line in content:
                if line.strip() == host_line.strip():
                    skip = True
                    continue
                if skip and not line.strip().startswith('Host '):
                    continue
                skip = False
                new_content.append(line)
            # Add new config
            config_entry = f"\n# {new_host} account\nHost github.com-{new_host}\n    HostName github.com\n    User git\n    IdentityFile {new_key}\n"
            new_content.append(config_entry)
            with open(self.ssh_config_path, 'w') as f:
                f.writelines(new_content)
            # Update email mapping
            if host in self.account_emails:
                del self.account_emails[host]
            self.account_emails[new_host] = new_email
            del self.accounts[host]
            self.accounts[new_host] = new_key
            # Update GUI
            self.account_var.set("Select Account")
            self.account_menu['menu'].delete(0, 'end')
            for account in self.accounts.keys():
                self.account_menu['menu'].add_command(label=account, command=tk._setit(self.account_var, account))
            self.update_key_list()
            # Save updated SSH config
            self.print_and_save_ssh_configs()
            messagebox.showinfo("Success", f"Updated configuration for github.com-{new_host}")
            edit_window.destroy()
        tk.Button(edit_window, text="Save", command=save_edit).grid(row=3, column=0, columnspan=2, pady=5)

    def generate_ssh_key(self):
        """Generate a new Ed25519 SSH key."""
        gen_window = tk.Toplevel(self.root)
        gen_window.title("Generate SSH Key")
        gen_window.geometry("400x250")
        
        tk.Label(gen_window, text="Key Name (e.g., joshua-personal):").grid(row=0, column=0, padx=5, pady=5)
        key_name_entry = tk.Entry(gen_window, width=30)
        key_name_entry.grid(row=0, column=1, padx=5, pady=5)
        key_name_entry.insert(0, "joshua-personal")
        
        tk.Label(gen_window, text="Email (e.g., joshua@personal.com):").grid(row=1, column=0, padx=5, pady=5)
        email_entry = tk.Entry(gen_window, width=30)
        email_entry.grid(row=1, column=1, padx=5, pady=5)
        email_entry.insert(0, "joshua@personal.com")
        
        tk.Label(gen_window, text="Passphrase (leave blank for none):").grid(row=2, column=0, padx=5, pady=5)
        passphrase_entry = tk.Entry(gen_window, width=30, show="*")
        passphrase_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def do_generate():
            key_name = key_name_entry.get().strip()
            email = email_entry.get().strip()
            passphrase = passphrase_entry.get().strip()
            
            if not key_name or not email:
                messagebox.showerror("Error", "Key name and email are required")
                return
                
            key_path = os.path.join(self.ssh_dir, key_name)
            if os.path.exists(key_path):
                messagebox.showerror("Error", f"Key {key_path} already exists")
                return
                
            try:
                # Ensure ~/.ssh exists
                os.makedirs(self.ssh_dir, exist_ok=True)
                
                # Generate key
                cmd = [
                    "ssh-keygen",
                    "-t", "ed25519",
                    "-C", email,
                    "-f", key_path,
                    "-N", passphrase
                ]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                # Start SSH agent and add key
                if platform.system() == "Windows":
                    subprocess.run(["powershell", "-Command", "Start-Service ssh-agent"], check=True)
                    subprocess.run(["ssh-add", key_path], check=True, capture_output=True, text=True)
                else:
                    subprocess.run(["eval", "$(ssh-agent -s)"], shell=True, check=True)
                    subprocess.run(["ssh-add", key_path], check=True, capture_output=True, text=True)
                
                # Store the email for this account
                self.account_emails[key_name] = email
                
                # Refresh key list
                self.keys = self.detect_ssh_keys()
                self.update_key_list()
                self.key_var.set("Select Key")
                key_menu = tk.OptionMenu(self.root, self.key_var, "Select Key", *self.keys)
                key_menu.grid(row=8, column=1, padx=5, pady=5)
                
                messagebox.showinfo("Success", f"Generated key {key_path}\nPublic key: {key_path}.pub\nAdd the public key to your GitHub account.")
                gen_window.destroy()
                
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to generate key: {e.stderr}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
        
        tk.Button(gen_window, text="Generate", command=do_generate).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(gen_window, text="Cancel", command=gen_window.destroy).grid(row=4, column=0, columnspan=2, pady=5)

    def open_ssh_folder(self):
        """Open the SSH key directory in File Explorer."""
        try:
            if os.path.exists(self.ssh_dir):
                os.startfile(self.ssh_dir)
            else:
                messagebox.showerror("Error", f"SSH directory {self.ssh_dir} does not exist")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open SSH directory: {str(e)}")

    def create_github_repo(self, owner, repo_name, token):
        """Create a GitHub repository using the API."""
        if not token:
            return False, "GitHub token required"
        url = f"https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "name": repo_name,
            "private": False  # Change to True for private repo
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                return True, "Repository created successfully"
            elif response.status_code == 422:
                return False, "Repository already exists or invalid name"
            else:
                return False, f"Failed to create repository: {response.json().get('message', 'Unknown error')}"
        except Exception as e:
            return False, f"Error creating repository: {str(e)}"

    def configure_new_project(self):
        """Configure a new project with no remote."""
        selected = self.repo_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a repository")
            return
        repo_path, account, _, _, email, protocol = self.repos[selected[0]]
        if account != "New Project (No Remote)":
            messagebox.showerror("Error", "Selected repository already has a remote")
            return
        
        config_window = tk.Toplevel(self.root)
        config_window.title("Configure New Project")
        config_window.geometry("400x300")
        
        tk.Label(config_window, text="GitHub Owner (e.g., josh-mds):").grid(row=0, column=0, padx=5, pady=5)
        owner_entry = tk.Entry(config_window, width=30)
        owner_entry.grid(row=0, column=1, padx=5, pady=5)
        owner_entry.insert(0, "josh-mds")
        
        tk.Label(config_window, text="Repository Name (e.g., new-project):").grid(row=1, column=0, padx=5, pady=5)
        repo_name_entry = tk.Entry(config_window, width=30)
        repo_name_entry.grid(row=1, column=1, padx=5, pady=5)
        repo_name_entry.insert(0, os.path.basename(repo_path))
        
        tk.Label(config_window, text="Select Account:").grid(row=2, column=0, padx=5, pady=5)
        account_var = tk.StringVar(config_window)
        account_var.set("joshua-personal" if "joshua-personal" in self.accounts else "Select Account")
        account_menu = tk.OptionMenu(config_window, account_var, "Select Account", *self.accounts.keys())
        account_menu.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(config_window, text="GitHub Token (optional, for auto-create):").grid(row=3, column=0, padx=5, pady=5)
        token_entry = tk.Entry(config_window, width=30, show="*")
        token_entry.grid(row=3, column=1, padx=5, pady=5)
        
        def do_configure():
            owner = owner_entry.get().strip()
            repo_name = repo_name_entry.get().strip()
            account = account_var.get().strip()
            token = token_entry.get().strip()
            
            if not owner or not repo_name or not account or account == "Select Account":
                messagebox.showerror("Error", "Owner, repository name, and account are required")
                return
                
            try:
                repo = Repo(repo_path)
                # Create remote
                remote_url = f"git@github.com-{account}:{owner}/{repo_name}.git"
                repo.create_remote("origin", remote_url)
                
                # Set user config, always use the email associated with the account
                account_email = self.account_emails.get(account, f"{account}@personal.com")
                with repo.config_writer() as config:
                    config.set_value("user", "name", account)
                    config.set_value("user", "email", account_email)
                
                # Save repo config
                config_path = os.path.join(repo.working_dir, '.git', 'config')
                print(f"\n=== Git Config for {repo.working_dir} ===")
                with open(config_path, 'r') as f:
                    content = f.read()
                    print(content)
                    repo_name_safe = repo.working_dir.replace(os.sep, '_').replace(':', '_').strip('_')
                    config_output = os.path.join(self.configs_dir, f"{repo_name_safe}_config.txt")
                    with open(config_output, 'w') as f_out:
                        f_out.write(content)
                
                # Update owner mapping
                self.owner_to_account[owner] = account
                
                # Create GitHub repo if token provided
                if token:
                    success, message = self.create_github_repo(owner, repo_name, token)
                    if not success:
                        messagebox.showerror("Error", message)
                        config_window.destroy()
                        self.scan_repos()
                        return
                
                # Refresh repo list
                self.scan_repos()
                
                # Provide instructions
                instructions = f"Configured {repo_path} for {account}\nRemote URL: {remote_url}\n"
                if token:
                    instructions += f"Repository created on GitHub.\nPush your project:\ncd {repo_path}\ngit add .\ngit commit -m 'Initial commit'\ngit push -u origin main"
                else:
                    instructions += f"Create the repository on GitHub at https://github.com/{owner}/{repo_name}\nThen push:\ncd {repo_path}\ngit add .\ngit commit -m 'Initial commit'\ngit push -u origin main"
                messagebox.showinfo("Success", instructions)
                config_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure project: {str(e)}")
        
        tk.Button(config_window, text="Configure", command=do_configure).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(config_window, text="Cancel", command=config_window.destroy).grid(row=5, column=0, columnspan=2, pady=5)

    def map_owner(self):
        """Map a GitHub owner to an account."""
        selected = self.repo_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a repository")
            return
        repo_path, account, origin_url, owner, email, protocol = self.repos[selected[0]]
        if account != "Unknown (Map Owner)":
            messagebox.showerror("Error", "Selected repository is not eligible for owner mapping")
            return
        
        # Parse URL to extract owner
        owner = None
        if origin_url.startswith('https://github.com/'):
            match = re.match(r'https://github\.com/([^/]+)/', origin_url)
            if match:
                owner = match.group(1)
        # Open a dialog to select account
        map_window = tk.Toplevel(self.root)
        map_window.title("Map GitHub Owner to Account")
        tk.Label(map_window, text=f"GitHub Owner: {owner or 'Unknown'}").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(map_window, text="Select Account:").grid(row=1, column=0, padx=5, pady=5)
        account_var = tk.StringVar(map_window)
        account_var.set("Select Account")
        account_menu = tk.OptionMenu(map_window, account_var, "Select Account", *self.accounts.keys())
        account_menu.grid(row=1, column=1, padx=5, pady=5)
        def save_mapping():
            account = account_var.get()
            if not account or account == "Select Account":
                messagebox.showerror("Error", "Please select a valid account")
                return
            if owner:
                self.owner_to_account[owner] = account
                messagebox.showinfo("Success", f"Mapped {owner} to {account}")
            else:
                messagebox.showerror("Error", "Cannot map non-GitHub repository")
            map_window.destroy()
            self.scan_repos()  # Refresh list
        tk.Button(map_window, text="Save", command=save_mapping).grid(row=2, column=0, columnspan=2, pady=5)

    def show_readme(self):
        """Show a popup with README instructions."""
        readme_window = tk.Toplevel(self.root)
        readme_window.title("GitHub Account Manager - README")
        readme_window.geometry("600x400")
        readme_window.resizable(True, True)

        # Text widget with scrollbar
        text_area = tk.Text(readme_window, wrap=tk.WORD, height=20, width=60)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(readme_window, command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.config(yscrollcommand=scrollbar.set)

        # README content
        readme_content = """
GitHub Account Manager - User Guide
==================================

This application helps you manage GitHub accounts for local Git repositories by generating SSH keys, configuring SSH, setting up new projects, and switching repository remotes between accounts.

Setup
-----
1. Ensure Git is installed on your system (includes Git Bash for Windows).
2. Install the required Python packages:
   - Run `pip install gitpython requests`
3. Generate an SSH key for your personal GitHub account:
   - In the app, go to the "Add Account" section and click "Generate SSH Key".
   - Enter:
     - Key Name: joshua-personal (default)
     - Email: joshua@personal.com (default)
     - Passphrase: Leave blank for none or enter a passphrase for extra security
   - Click "Generate" to create the key in C:\\Users\\joshu\\.ssh\\joshua-personal (private) and joshua-personal.pub (public).
   - The key is automatically added to the SSH agent.
   - The email you enter (e.g., joshua@personal.com) will be used for new projects configured with this account.
4. Add the public key to your GitHub account:
   - Click "Open SSH Folder" to access C:\\Users\\joshu\\.ssh in File Explorer.
   - Copy the public key:
     ```
     Get-Content C:\\Users\\joshu\\.ssh\\joshua-personal.pub
     ```
   - Go to GitHub → Settings → SSH and GPG keys → New SSH key, paste the key, and save (e.g., title it "Joshua Personal").
5. (Optional) Create a GitHub personal access token for auto-creating repositories:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic).
   - Generate a token with `repo` scope.
   - Copy the token for use in the app.

New Projects
------------
For new projects with only a .git folder (e.g., created with `git init`):
1. Scan the project folder:
   - Click "Browse" to select the folder (e.g., C:\\Users\\joshu\\Documents\\code). The last scanned folder is remembered.
   - Click "Scan Repos" to list the project (e.g., C:\\Users\\joshu\\Documents\\code\\new-project -> New Project (No Remote)).
2. Configure the project:
   - Select the project and click "Configure New Project".
   - Enter:
     - GitHub Owner: josh-mds (default)
     - Repository Name: new-project (default, based on folder name)
     - Account: joshua-personal
     - GitHub Token: (optional, for auto-creating the repo)
   - Click "Configure" to set the remote URL (e.g., git@github.com-joshua-personal:josh-mds/new-project.git).
   - The email associated with the account (e.g., joshua@personal.com for joshua-personal) will be set in the repo's .git/config.
3. Follow the instructions:
   - If a token was provided, the repo is created automatically.
   - Otherwise, create the repo manually at https://github.com/josh-mds/new-project.
   - Push the project:
     ```
     cd C:\\Users\\joshu\\Documents\\code\\new-project
     git add .
     git commit -m "Initial commit"
     git push -u origin main
     ```

Using the Application
--------------------
1. Launch the app:
   - Run `python github_account_manager.py`
   - The last scanned folder (e.g., C:\\Users\\joshu\\Documents\\code) is pre-populated in the folder field.
2. Add SSH Configurations:
   - In the "New Account Host" field, enter a host alias (e.g., joshua-personal).
   - Select the SSH key (e.g., C:\\Users\\joshu\\.ssh\\joshua-personal) from the dropdown.
   - Click "Add Account" to create an entry in C:\\Users\\joshu\\.ssh\\config.
   - Click "Refresh" to update the SSH keys and accounts list.
3. Access SSH Keys:
   - Click "Open SSH Folder" to open C:\\Users\\joshu\\.ssh in File Explorer to view or copy keys (e.g., joshua-personal.pub).
4. Scan Repositories:
   - Click "Browse" to select a folder (e.g., C:\\Users\\joshu\\Documents\\code).
   - Click "Scan Repos" to list all Git repositories. The folder is saved for next time.
   - Click "Refresh" to update the repository list (e.g., after configuring a new project or pushing).
   - Each repo shows:
     - Path
     - Account (e.g., Unknown, joshua-personal, New Project (No Remote), or Non-GitHub)
     - Protocol (https, ssh, none, or other)
     - Owner (e.g., josh-mds)
     - Email (from .git/config, if set)
5. Map Owners to Accounts:
   - For repos with "Unknown (Map Owner)", select the repo and click "Map Owner to Account".
   - Choose an account (e.g., joshua-personal) and save to associate the GitHub owner (e.g., josh-mds) with the account.
6. Switch Repository Account:
   - Select a repo and an account from the dropdown.
   - Click "Switch Account" to change the remote URL to SSH (e.g., git@github.com-joshua-personal:josh-mds/repo.git).
7. Edit/Delete SSH Configurations:
   - Select a key in the "SSH Keys" list.
   - Click "Edit Config" to modify the host, key, or email.
   - Click "Delete Config" to remove the configuration.

Debugging
---------
- Check the terminal for SSH keys, ~/.ssh/config, and each repo’s .git/config.
- Inspect the `configs` folder for saved configurations:
  - `ssh_config.txt`: Latest ~/.ssh/config
  - `<repo_path>_config.txt`: Latest .git/config for each repo
- Check `config.json` for the last scanned folder path.
- If repos show "Unknown", ensure SSH configs are added and owners are mapped.
- For non-GitHub repos (e.g., AWS CodeCommit), the app labels them "Non-GitHub".

Troubleshooting
---------------
- No SSH keys detected? Generate a key using the "Generate SSH Key" button and click "Refresh".
- Can't find keys? Click "Open SSH Folder" to verify C:\\Users\\joshu\\.ssh.
- No ~/.ssh/config? Add accounts via the app to create it.
- "Unknown (Map Owner)" persists? Map the owner to an account.
- Errors configuring new projects? Ensure the owner and repo name are valid.
- GUI outdated? Click "Refresh" to update repositories and keys.
- Commits tied to wrong account? Check the user.email in .git/config and update it to match your account (e.g., joshua@personal.com for joshua-personal).
- SSH issues? Test the connection:
  ```
  ssh -T git@github.com-joshua-personal
  ```

For issues, check the terminal output or contact your developer.
"""
        text_area.insert(tk.END, readme_content)
        text_area.config(state=tk.DISABLED)  # Make text read-only

        # Close button
        tk.Button(readme_window, text="Close", command=readme_window.destroy).pack(pady=5)

    def update_key_list(self):
        """Update the key list display."""
        self.key_list.delete(0, tk.END)
        for key in self.keys:
            account = None
            for host, path in self.accounts.items():
                if path == key:
                    account = host
                    break
            display = f"{key} -> {account if account else 'Not used'}"
            self.key_list.insert(tk.END, display)

    def refresh(self):
        """Refresh the repository and key lists."""
        folder = self.folder_entry.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder before refreshing")
            return
        self.scan_repos()

    def scan_repos(self):
        """Scan the specified folder for Git repositories and their accounts."""
        folder = self.folder_entry.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return
        self.repos = []
        self.repo_list.delete(0, tk.END)
        self.keys = self.detect_ssh_keys()  # Refresh keys
        self.accounts = self.load_ssh_configs()  # Refresh accounts
        self.update_key_list()  # Update key list
        for root, dirs, _ in os.walk(folder):
            if '.git' in dirs:
                repo_path = os.path.join(root, '.git')
                try:
                    repo = Repo(repo_path, search_parent_directories=True)
                    email = repo.config_reader().get_value("user", "email", "Unknown")
                    origin_url = repo.remotes.origin.url if 'origin' in repo.remotes else None
                    if origin_url:
                        account = "Unknown"
                        owner = None
                        protocol = "other"
                        # Handle SSH URLs
                        match_ssh = re.match(r'git@github\.com-(\S+?):', origin_url)
                        if match_ssh:
                            account = match_ssh.group(1)
                            protocol = "ssh"
                        # Handle HTTPS URLs
                        elif origin_url.startswith('https://github.com/'):
                            match_https = re.match(r'https://github\.com/([^/]+)/', origin_url)
                            if match_https:
                                owner = match_https.group(1)
                                account = self.owner_to_account.get(owner, "Unknown (Map Owner)")
                                protocol = "https"
                        # Handle non-GitHub URLs
                        else:
                            account = "Non-GitHub"
                            protocol = "other"
                        self.repos.append((repo.working_dir, account, origin_url, owner, email, protocol))
                        display = f"{repo.working_dir} -> {account} (Protocol: {protocol}, Owner: {owner or 'N/A'}, Email: {email})"
                    else:
                        # New project with no remote
                        account = "New Project (No Remote)"
                        protocol = "none"
                        self.repos.append((repo.working_dir, account, None, None, email, protocol))
                        display = f"{repo.working_dir} -> {account} (Protocol: {protocol}, Owner: N/A, Email: {email})"
                    self.repo_list.insert(tk.END, display)
                    # Print and save repo config
                    config_path = os.path.join(repo.working_dir, '.git', 'config')
                    print(f"\n=== Git Config for {repo.working_dir} ===")
                    with open(config_path, 'r') as f:
                        content = f.read()
                        print(content)
                        # Save to configs folder
                        repo_name = repo.working_dir.replace(os.sep, '_').replace(':', '_').strip('_')
                        config_output = os.path.join(self.configs_dir, f"{repo_name}_config.txt")
                        with open(config_output, 'w') as f_out:
                            f_out.write(content)
                except Exception as e:
                    print(f"Error scanning {repo_path}: {e}")
        if not self.repos:
            messagebox.showinfo("Info", "No Git repositories found in the folder")
        # Save the scanned folder path
        self.save_last_scanned_path(folder)

    def add_account(self):
        """Add a new GitHub account to SSH config."""
        host = self.host_entry.get()
        identity_file = self.key_var.get()
        if not host or not identity_file or identity_file == "Select Key":
            messagebox.showerror("Error", "Please enter host and select a key")
            return
        if not os.path.exists(identity_file):
            messagebox.showerror("Error", "Identity file does not exist")
            return
        if host not in self.account_emails:
            messagebox.showinfo("Info", f"No email associated with {host}. Please set one.")
            # Open a dialog to set email
            email_window = tk.Toplevel(self.root)
            email_window.title("Set Email for Account")
            tk.Label(email_window, text=f"Email for {host}:").grid(row=0, column=0, padx=5, pady=5)
            email_entry = tk.Entry(email_window, width=30)
            email_entry.grid(row=0, column=1, padx=5, pady=5)
            email_entry.insert(0, f"{host}@personal.com")
            def save_email():
                email = email_entry.get().strip()
                if not email:
                    messagebox.showerror("Error", "Email is required")
                    return
                self.account_emails[host] = email
                self.save_ssh_config(host, identity_file)
                messagebox.showinfo("Success", f"Added account github.com-{host} with email {email}")
                self.host_entry.delete(0, tk.END)
                self.key_var.set("Select Key")
                email_window.destroy()
            tk.Button(email_window, text="Save", command=save_email).grid(row=1, column=0, columnspan=2, pady=5)
        else:
            self.save_ssh_config(host, identity_file)
            messagebox.showinfo("Success", f"Added account github.com-{host} with email {self.account_emails[host]}")
            self.host_entry.delete(0, tk.END)
            self.key_var.set("Select Key")

    def switch_account(self):
        """Switch the selected repository's remote to a different account."""
        selected = self.repo_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a repository")
            return
        new_account = self.account_var.get()
        if not new_account or new_account == "Select Account":
            messagebox.showerror("Error", "Please select a valid account")
            return
        repo_path, account, old_url, owner, email, protocol = self.repos[selected[0]]
        if account == "New Project (No Remote)":
            messagebox.showerror("Error", "Use 'Configure New Project' for repositories without a remote")
            return
        try:
            repo = Repo(repo_path)
            # Parse old URL to get owner/repo
            match = re.match(r'(?:git@github\.com-\S+?:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?$', old_url)
            if not match:
                messagebox.showerror("Error", "Invalid remote URL format")
                return
            repo_part = match.group(1)
            new_url = f"git@github.com-{new_account}:{repo_part}.git"
            repo.remotes.origin.set_url(new_url)
            # Update user.email and user.name
            account_email = self.account_emails.get(new_account, f"{new_account}@personal.com")
            with repo.config_writer() as config:
                config.set_value("user", "email", account_email)
                config.set_value("user", "name", new_account)
            # Update owner mapping if owner exists
            if owner:
                self.owner_to_account[owner] = new_account
            # Save updated repo config
            config_path = os.path.join(repo.working_dir, '.git', 'config')
            print(f"\n=== Updated Git Config for {repo.working_dir} ===")
            with open(config_path, 'r') as f:
                content = f.read()
                print(content)
                # Save to configs folder
                repo_name = repo.working_dir.replace(os.sep, '_').replace(':', '_').strip('_')
                config_output = os.path.join(self.configs_dir, f"{repo_name}_config.txt")
                with open(config_output, 'w') as f_out:
                    f_out.write(content)
            self.scan_repos()  # Refresh list
            messagebox.showinfo("Success", f"Switched {repo_path} to {new_account}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch account: {e}")

    def select_folder(self):
        """Open a folder selection dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.save_last_scanned_path(folder)

    def setup_gui(self):
        """Setup the tkinter GUI."""
        # Folder selection
        tk.Label(self.root, text="Folder Path:").grid(row=0, column=0, padx=5, pady=5)
        self.folder_entry = tk.Entry(self.root, width=50)
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5)
        if self.last_scanned_path:
            self.folder_entry.insert(0, self.last_scanned_path)
        tk.Button(self.root, text="Browse", command=self.select_folder).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(self.root, text="Scan Repos", command=self.scan_repos).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(self.root, text="Refresh", command=self.refresh).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(self.root, text="Information", command=self.show_readme).grid(row=0, column=5, padx=5, pady=5)

        # Repository list
        tk.Label(self.root, text="Repositories:").grid(row=1, column=0, padx=5, pady=5)
        self.repo_list = tk.Listbox(self.root, width=120, height=10)
        self.repo_list.grid(row=2, column=0, columnspan=6, padx=5, pady=5)
        tk.Button(self.root, text="Map Owner to Account", command=self.map_owner).grid(row=3, column=0, padx=5, pady=5)
        tk.Button(self.root, text="Configure New Project", command=self.configure_new_project).grid(row=3, column=1, padx=5, pady=5)

        # SSH Keys list
        tk.Label(self.root, text="SSH Keys:").grid(row=4, column=0, padx=5, pady=5)
        self.key_list = tk.Listbox(self.root, width=80, height=5)
        self.key_list.grid(row=5, column=0, columnspan=6, padx=5, pady=5)
        tk.Button(self.root, text="Edit Config", command=self.edit_ssh_config).grid(row=6, column=0, padx=5, pady=5)
        tk.Button(self.root, text="Delete Config", command=self.delete_ssh_config).grid(row=6, column=1, padx=5, pady=5)
        self.update_key_list()

        # Add account
        tk.Label(self.root, text="New Account Host (e.g., joshua-personal):").grid(row=7, column=0, padx=5, pady=5)
        self.host_entry = tk.Entry(self.root, width=20)
        self.host_entry.grid(row=7, column=1, padx=5, pady=5)
        tk.Label(self.root, text="Select SSH Key:").grid(row=8, column=0, padx=5, pady=5)
        self.key_var = tk.StringVar(self.root)
        self.key_var.set("Select Key")
        key_menu = tk.OptionMenu(self.root, self.key_var, "Select Key", *self.keys)
        key_menu.grid(row=8, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Add Account", command=self.add_account).grid(row=8, column=2, padx=5, pady=5)
        tk.Button(self.root, text="Generate SSH Key", command=self.generate_ssh_key).grid(row=8, column=3, padx=5, pady=5)
        tk.Button(self.root, text="Open SSH Folder", command=self.open_ssh_folder).grid(row=8, column=4, padx=5, pady=5)

        # Switch account
        tk.Label(self.root, text="Switch Selected Repo to Account:").grid(row=9, column=0, padx=5, pady=5)
        self.account_var = tk.StringVar(self.root)
        self.account_var.set("Select Account")
        self.account_menu = tk.OptionMenu(self.root, self.account_var, "Select Account")
        self.account_menu.grid(row=9, column=1, padx=5, pady=5)
        for account in self.accounts.keys():
            self.account_menu['menu'].add_command(label=account, command=tk._setit(self.account_var, account))
        tk.Button(self.root, text="Switch Account", command=self.switch_account).grid(row=9, column=2, padx=5, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(True, True)
    app = GitHubAccountManager(root)
    root.mainloop()