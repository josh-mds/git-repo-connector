import json
import shutil
import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional

class BackupManager:
    """Manages configuration backups and recovery"""
    
    def __init__(self, app):
        self.app = app
        self.backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, description: str = "") -> str:
        """Create a backup of current configuration"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        backup_data = {
            "timestamp": timestamp,
            "description": description,
            "config": {
                "accounts": {name: {
                    "name": acc.name,
                    "email": acc.email,
                    "ssh_key_path": acc.ssh_key_path,
                    "github_username": acc.github_username
                } for name, acc in self.app.accounts.items()},
                "last_scanned_path": self.app.last_scanned_path
            }
        }
        
        # Save configuration
        with open(os.path.join(backup_path, "config.json"), 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Backup SSH config if it exists
        if os.path.exists(self.app.ssh_config_path):
            shutil.copy2(self.app.ssh_config_path, 
                        os.path.join(backup_path, "ssh_config"))
        
        # Backup SSH keys
        keys_dir = os.path.join(backup_path, "ssh_keys")
        os.makedirs(keys_dir, exist_ok=True)
        
        for account in self.app.accounts.values():
            if os.path.exists(account.ssh_key_path):
                shutil.copy2(account.ssh_key_path, keys_dir)
                pub_key = f"{account.ssh_key_path}.pub"
                if os.path.exists(pub_key):
                    shutil.copy2(pub_key, keys_dir)
        
        return backup_path
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for item in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, item)
            config_file = os.path.join(backup_path, "config.json")
            
            if os.path.isdir(backup_path) and os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                    
                    backups.append({
                        "name": item,
                        "path": backup_path,
                        "timestamp": data.get("timestamp", "Unknown"),
                        "description": data.get("description", ""),
                        "accounts": len(data.get("config", {}).get("accounts", {}))
                    })
                except Exception:
                    continue
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            config_file = os.path.join(backup_path, "config.json")
            
            with open(config_file, 'r') as f:
                backup_data = json.load(f)
            
            # Create backup of current state first
            self.create_backup("Before restore")
            
            # Clear current accounts
            self.app.accounts.clear()
            
            # Restore configuration
            config = backup_data.get("config", {})
            self.app.last_scanned_path = config.get("last_scanned_path", "")
            
            # Restore accounts
            for name, acc_data in config.get("accounts", {}).items():
                account = Account(
                    name=acc_data["name"],
                    email=acc_data["email"],
                    ssh_key_path=acc_data["ssh_key_path"],
                    github_username=acc_data.get("github_username")
                )
                self.app.accounts[name] = account
            
            # Restore SSH config
            ssh_config_backup = os.path.join(backup_path, "ssh_config")
            if os.path.exists(ssh_config_backup):
                shutil.copy2(ssh_config_backup, self.app.ssh_config_path)
            
            # Restore SSH keys
            keys_dir = os.path.join(backup_path, "ssh_keys")
            if os.path.exists(keys_dir):
                for key_file in os.listdir(keys_dir):
                    src = os.path.join(keys_dir, key_file)
                    dst = os.path.join(self.app.ssh_dir, key_file)
                    shutil.copy2(src, dst)
                    
                    # Set correct permissions on Unix-like systems
                    if os.name != 'nt' and not key_file.endswith('.pub'):
                        os.chmod(dst, 0o600)
            
            # Save restored configuration
            self.app.save_config()
            
            return True
        
        except Exception as e:
            self.app.show_error(f"Failed to restore backup: {e}")
            return False

class RecoveryWizard:
    """Guided recovery wizard for fixing common issues"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.backup_manager = BackupManager(app)
        self.window = None
    
    def show(self):
        """Show recovery wizard"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Recovery Wizard")
        self.window.geometry("500x400")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.show_recovery_options()
    
    def show_recovery_options(self):
        """Show recovery options"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        tk.Label(self.window, text="Recovery Wizard", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        tk.Label(self.window, text="What would you like to do?", 
                font=('Arial', 12)).pack(pady=10)
        
        options_frame = tk.Frame(self.window)
        options_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Recovery options
        tk.Button(options_frame, text="🔧 Fix Configuration Issues", 
                 command=self.run_health_check,
                 width=30, pady=5).pack(pady=5)
        
        tk.Button(options_frame, text="💾 Create Backup", 
                 command=self.create_backup_dialog,
                 width=30, pady=5).pack(pady=5)
        
        tk.Button(options_frame, text="🔄 Restore from Backup", 
                 command=self.show_backup_list,
                 width=30, pady=5).pack(pady=5)
        
        tk.Button(options_frame, text="🚨 Emergency Reset", 
                 command=self.emergency_reset,
                 width=30, pady=5).pack(pady=5)
        
        tk.Button(options_frame, text="📋 Export Debug Info", 
                 command=self.export_debug_info,
                 width=30, pady=5).pack(pady=5)
        
        # Close button
        tk.Button(self.window, text="Close", 
                 command=self.window.destroy).pack(pady=20)
    
    def run_health_check(self):
        """Run configuration health check"""
        self.window.destroy()
        health_check = HealthCheckDialog(self.parent, self.app)
        health_check.show()
    
    def create_backup_dialog(self):
        """Show backup creation dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Backup")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="Create Configuration Backup", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        tk.Label(dialog, text="Description (optional):").pack(pady=5)
        desc_entry = tk.Entry(dialog, width=40)
        desc_entry.pack(pady=5)
        
        def create_backup():
            description = desc_entry.get().strip()
            
            try:
                backup_path = self.backup_manager.create_backup(description)
                messagebox.showinfo("Backup Created", 
                                   f"Backup created successfully:\n{backup_path}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Backup Failed", f"Failed to create backup: {e}")
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Create Backup", 
                 command=create_backup).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", 
                 command=dialog.destroy).pack(side='left', padx=5)
    
    def show_backup_list(self):
        """Show list of available backups"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        tk.Label(self.window, text="Restore from Backup", 
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        # List backups
        backups = self.backup_manager.list_backups()
        
        if not backups:
            tk.Label(self.window, text="No backups found", 
                    fg='gray').pack(pady=20)
            tk.Button(self.window, text="Back", 
                     command=self.show_recovery_options).pack(pady=10)
            return
        
        # Backup list
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview for backups
        columns = ('Date', 'Description', 'Accounts')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        tree.heading('Date', text='Date')
        tree.heading('Description', text='Description')
        tree.heading('Accounts', text='Accounts')
        
        tree.column('Date', width=150)
        tree.column('Description', width=200)
        tree.column('Accounts', width=80)
        
        for backup in backups:
            # Format timestamp
            try:
                dt = datetime.datetime.strptime(backup['timestamp'], "%Y%m%d_%H%M%S")
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = backup['timestamp']
            
            tree.insert('', 'end', values=(
                formatted_date,
                backup['description'] or 'No description',
                backup['accounts']
            ), tags=(backup['path'],))
        
        tree.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        def restore_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Error", "Please select a backup to restore")
                return
            
            backup_path = tree.item(selection[0])['tags'][0]
            
            if messagebox.askyesno("Confirm Restore", 
                                  "This will replace your current configuration.\n"
                                  "A backup of the current state will be created first.\n\n"
                                  "Continue?"):
                if self.backup_manager.restore_backup(backup_path):
                    messagebox.showinfo("Restore Complete", 
                                       "Configuration restored successfully!")
                    self.app.refresh_accounts_list()
                    self.window.destroy()
        
        tk.Button(button_frame, text="Restore Selected", 
                 command=restore_selected).pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", 
                 command=self.show_recovery_options).pack(side='left', padx=5)
    
    def emergency_reset(self):
        """Perform emergency reset of configuration"""
        if messagebox.askyesno("Emergency Reset", 
                              "This will:\n"
                              "• Create a backup of current configuration\n"
                              "• Reset all accounts and settings\n"
                              "• Keep SSH keys but reset SSH config\n\n"
                              "Continue?"):
            try:
                # Create backup first
                self.backup_manager.create_backup("Before emergency reset")
                
                # Clear accounts
                self.app.accounts.clear()
                
                # Reset paths
                self.app.last_scanned_path = ""
                
                # Reset SSH config (but keep backup)
                if os.path.exists(self.app.ssh_config_path):
                    shutil.copy2(self.app.ssh_config_path, 
                                f"{self.app.ssh_config_path}.backup")
                    os.remove(self.app.ssh_config_path)
                
                # Save clean configuration
                self.app.save_config()
                
                # Refresh UI
                self.app.refresh_accounts_list()
                
                messagebox.showinfo("Reset Complete", 
                                   "Emergency reset completed.\n"
                                   "You can now run the setup wizard to reconfigure.")
                
                self.window.destroy()
                self.app.show_setup_wizard()
                
            except Exception as e:
                messagebox.showerror("Reset Failed", f"Emergency reset failed: {e}")
    
    def export_debug_info(self):
        """Export debug information for troubleshooting"""
        from tkinter import filedialog
        
        export_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Debug Information"
        )
        
        if not export_path:
            return
        
        try:
            debug_info = self.collect_debug_info()
            
            with open(export_path, 'w') as f:
                f.write(debug_info)
            
            messagebox.showinfo("Export Complete", 
                               f"Debug information exported to:\n{export_path}")
        
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export debug info: {e}")
    
    def collect_debug_info(self) -> str:
        """Collect comprehensive debug information"""
        info = []
        
        info.append("=== GitHub Account Manager Debug Information ===")
        info.append(f"Generated: {datetime.datetime.now()}")
        info.append(f"Platform: {platform.system()} {platform.release()}")
        info.append("")
        
        # System info
        info.append("=== System Information ===")
        git_ok, git_msg = DependencyChecker.check_git()
        ssh_ok, ssh_msg = DependencyChecker.check_ssh()
        py_ok, py_msg = DependencyChecker.check_python_deps()
        
        info.append(f"Git: {'OK' if git_ok else 'FAILED'} - {git_msg}")
        info.append(f"SSH: {'OK' if ssh_ok else 'FAILED'} - {ssh_msg}")
        info.append(f"Python Dependencies: {'OK' if py_ok else 'FAILED'} - {py_msg}")
        info.append("")
        
        # Configuration
        info.append("=== Configuration ===")
        info.append(f"SSH Directory: {self.app.ssh_dir}")
        info.append(f"SSH Config Path: {self.app.ssh_config_path}")
        info.append(f"Config File: {self.app.config_file}")
        info.append(f"Last Scanned Path: {self.app.last_scanned_path}")
        info.append("")
        
        # Accounts
        info.append("=== Accounts ===")
        for name, account in self.app.accounts.items():
            info.append(f"Account: {name}")
            info.append(f"  Email: {account.email}")
            info.append(f"  SSH Key: {account.ssh_key_path}")
            info.append(f"  Key Exists: {os.path.exists(account.ssh_key_path)}")
            info.append(f"  Public Key Exists: {os.path.exists(f'{account.ssh_key_path}.pub')}")
            info.append(f"  GitHub Username: {account.github_username or 'Not set'}")
            info.append("")
        
        # SSH Config
        info.append("=== SSH Configuration ===")
        if os.path.exists(self.app.ssh_config_path):
            try:
                with open(self.app.ssh_config_path, 'r') as f:
                    info.append(f.read())
            except Exception as e:
                info.append(f"Error reading SSH config: {e}")
        else:
            info.append("SSH config file does not exist")
        info.append("")
        
        # Validation results
        info.append("=== Validation Results ===")
        try:
            validator = ConfigurationValidator(self.app)
            results = validator.validate_all()
            
            for result in results:
                status = "PASS" if result.is_valid else "FAIL"
                info.append(f"[{status}] {result.message}")
                if not result.is_valid and result.fix_suggestion:
                    info.append(f"  Fix: {result.fix_suggestion}")
            
        except Exception as e:
            info.append(f"Error running validation: {e}")
        
        return "\n".join(info)