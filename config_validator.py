import os
import subprocess
from typing import List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    fix_suggestion: str = ""
    severity: str = "error"  # error, warning, info

class ConfigurationValidator:
    """Validates and fixes common configuration issues"""
    
    def __init__(self, app):
        self.app = app
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks"""
        results = []
        
        # Check SSH directory and permissions
        results.extend(self.validate_ssh_setup())
        
        # Check SSH keys
        results.extend(self.validate_ssh_keys())
        
        # Check SSH config
        results.extend(self.validate_ssh_config())
        
        # Check GitHub connectivity
        results.extend(self.validate_github_connectivity())
        
        # Check Git configuration
        results.extend(self.validate_git_config())
        
        return results
    
    def validate_ssh_setup(self) -> List[ValidationResult]:
        """Validate SSH directory and permissions"""
        results = []
        
        # Check if .ssh directory exists
        if not os.path.exists(self.app.ssh_dir):
            results.append(ValidationResult(
                is_valid=False,
                message="SSH directory does not exist",
                fix_suggestion="Create ~/.ssh directory with proper permissions",
                severity="error"
            ))
            return results
        
        # Check permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            stat_info = os.stat(self.app.ssh_dir)
            if stat_info.st_mode & 0o777 != 0o700:
                results.append(ValidationResult(
                    is_valid=False,
                    message="SSH directory has incorrect permissions",
                    fix_suggestion="Run: chmod 700 ~/.ssh",
                    severity="warning"
                ))
        
        results.append(ValidationResult(
            is_valid=True,
            message="SSH directory is properly configured",
            severity="info"
        ))
        
        return results
    
    def validate_ssh_keys(self) -> List[ValidationResult]:
        """Validate SSH key files"""
        results = []
        
        for account in self.app.accounts.values():
            # Check if private key exists
            if not os.path.exists(account.ssh_key_path):
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"Private key missing for {account.name}",
                    fix_suggestion=f"Regenerate SSH key for {account.name}",
                    severity="error"
                ))
                continue
            
            # Check if public key exists
            pub_key_path = f"{account.ssh_key_path}.pub"
            if not os.path.exists(pub_key_path):
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"Public key missing for {account.name}",
                    fix_suggestion=f"Regenerate SSH key pair for {account.name}",
                    severity="error"
                ))
                continue
            
            # Check key permissions (Unix-like systems)
            if os.name != 'nt':
                stat_info = os.stat(account.ssh_key_path)
                if stat_info.st_mode & 0o777 != 0o600:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Private key has incorrect permissions for {account.name}",
                        fix_suggestion=f"Run: chmod 600 {account.ssh_key_path}",
                        severity="warning"
                    ))
            
            # Check if key is loaded in SSH agent
            if not self.is_key_in_agent(account.ssh_key_path):
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"SSH key not loaded in agent for {account.name}",
                    fix_suggestion=f"Run: ssh-add {account.ssh_key_path}",
                    severity="warning"
                ))
            
            results.append(ValidationResult(
                is_valid=True,
                message=f"SSH key is valid for {account.name}",
                severity="info"
            ))
        
        return results
    
    def validate_ssh_config(self) -> List[ValidationResult]:
        """Validate SSH configuration file"""
        results = []
        
        if not os.path.exists(self.app.ssh_config_path):
            results.append(ValidationResult(
                is_valid=False,
                message="SSH config file does not exist",
                fix_suggestion="Create SSH config by adding an account",
                severity="warning"
            ))
            return results
        
        # Parse SSH config and check for our accounts
        try:
            with open(self.app.ssh_config_path, 'r') as f:
                config_content = f.read()
            
            for account in self.app.accounts.values():
                host_pattern = f"Host github.com-{account.name}"
                if host_pattern not in config_content:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"SSH config missing for {account.name}",
                        fix_suggestion=f"Add SSH config entry for {account.name}",
                        severity="error"
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=True,
                        message=f"SSH config is valid for {account.name}",
                        severity="info"
                    ))
        
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Error reading SSH config: {e}",
                fix_suggestion="Check SSH config file permissions and syntax",
                severity="error"
            ))
        
        return results
    
    def validate_github_connectivity(self) -> List[ValidationResult]:
        """Test GitHub connectivity for each account"""
        results = []
        
        for account in self.app.accounts.values():
            try:
                # Test SSH connection to GitHub
                cmd = ["ssh", "-T", f"git@github.com-{account.name}", "-o", "ConnectTimeout=10"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if "successfully authenticated" in result.stderr:
                    results.append(ValidationResult(
                        is_valid=True,
                        message=f"GitHub connection successful for {account.name}",
                        severity="info"
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"GitHub authentication failed for {account.name}",
                        fix_suggestion="Check if public key is added to GitHub account",
                        severity="error"
                    ))
            
            except subprocess.TimeoutExpired:
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"GitHub connection timeout for {account.name}",
                    fix_suggestion="Check internet connection and SSH configuration",
                    severity="warning"
                ))
            
            except Exception as e:
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"GitHub connection error for {account.name}: {e}",
                    fix_suggestion="Check SSH setup and GitHub configuration",
                    severity="error"
                ))
        
        return results
    
    def validate_git_config(self) -> List[ValidationResult]:
        """Validate Git global configuration"""
        results = []
        
        try:
            # Check global Git config
            name_result = subprocess.run(["git", "config", "--global", "user.name"], 
                                       capture_output=True, text=True)
            email_result = subprocess.run(["git", "config", "--global", "user.email"], 
                                        capture_output=True, text=True)
            
            if name_result.returncode == 0 and email_result.returncode == 0:
                results.append(ValidationResult(
                    is_valid=True,
                    message="Git global configuration is set",
                    severity="info"
                ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    message="Git global configuration is incomplete",
                    fix_suggestion="Set global Git user name and email",
                    severity="warning"
                ))
        
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Error checking Git configuration: {e}",
                fix_suggestion="Ensure Git is properly installed",
                severity="error"
            ))
        
        return results
    
    def is_key_in_agent(self, key_path: str) -> bool:
        """Check if SSH key is loaded in SSH agent"""
        try:
            result = subprocess.run(["ssh-add", "-l"], capture_output=True, text=True)
            return key_path in result.stdout
        except:
            return False
    
    def auto_fix_issue(self, result: ValidationResult) -> bool:
        """Attempt to automatically fix an issue"""
        try:
            if "SSH directory does not exist" in result.message:
                os.makedirs(self.app.ssh_dir, mode=0o700, exist_ok=True)
                return True
            
            elif "SSH directory has incorrect permissions" in result.message:
                if os.name != 'nt':
                    os.chmod(self.app.ssh_dir, 0o700)
                    return True
            
            elif "Private key has incorrect permissions" in result.message:
                if os.name != 'nt':
                    # Extract key path from message or use other method
                    for account in self.app.accounts.values():
                        if os.path.exists(account.ssh_key_path):
                            os.chmod(account.ssh_key_path, 0o600)
                    return True
            
            elif "SSH key not loaded in agent" in result.message:
                for account in self.app.accounts.values():
                    if os.path.exists(account.ssh_key_path):
                        subprocess.run(["ssh-add", account.ssh_key_path], 
                                     capture_output=True, text=True)
                return True
            
            return False
        
        except Exception:
            return False

# Integration with the main app
class HealthCheckDialog:
    """Dialog to show configuration health check results"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.validator = ConfigurationValidator(app)
        self.window = None
    
    def show(self):
        """Show health check dialog"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Configuration Health Check")
        self.window.geometry("600x500")
        self.window.transient(self.parent)
        
        # Run validation
        progress = ProgressDialog(self.parent, "Running Health Check...")
        
        def run_validation():
            return self.validator.validate_all()
        
        def on_validation_complete(results):
            progress.close()
            self.display_results(results)
        
        self.app.run_async_operation(run_validation, on_validation_complete)
    
    def display_results(self, results: List[ValidationResult]):
        """Display validation results"""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Header
        header_frame = tk.Frame(self.window)
        header_frame.pack(fill='x', pady=10)
        
        tk.Label(header_frame, text="Configuration Health Check", 
                font=('Arial', 16, 'bold')).pack()
        
        # Summary
        errors = sum(1 for r in results if not r.is_valid and r.severity == "error")
        warnings = sum(1 for r in results if not r.is_valid and r.severity == "warning")
        
        summary_text = f"Found {errors} errors and {warnings} warnings"
        color = "red" if errors > 0 else "orange" if warnings > 0 else "green"
        
        tk.Label(header_frame, text=summary_text, fg=color, 
                font=('Arial', 12)).pack()
        
        # Results list
        results_frame = tk.Frame(self.window)
        results_frame.pack(fill='both', expand=True, pady=10, padx=10)
        
        # Treeview for results
        columns = ('Status', 'Message', 'Suggestion')
        tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        tree.heading('Status', text='Status')
        tree.heading('Message', text='Message')
        tree.heading('Suggestion', text='Fix Suggestion')
        
        tree.column('Status', width=80)
        tree.column('Message', width=250)
        tree.column('Suggestion', width=250)
        
        for result in results:
            status_icon = "✅" if result.is_valid else ("❌" if result.severity == "error" else "⚠️")
            tree.insert('', 'end', values=(
                status_icon,
                result.message,
                result.fix_suggestion
            ))
        
        tree.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill='x', pady=10)
        
        tk.Button(button_frame, text="Auto-Fix Issues", 
                 command=lambda: self.auto_fix_all(results)).pack(side='left', padx=5)
        tk.Button(button_frame, text="Re-run Check", 
                 command=self.show).pack(side='left', padx=5)
        tk.Button(button_frame, text="Close", 
                 command=self.window.destroy).pack(side='right', padx=5)
    
    def auto_fix_all(self, results: List[ValidationResult]):
        """Attempt to auto-fix all fixable issues"""
        fixed_count = 0
        
        for result in results:
            if not result.is_valid and self.validator.auto_fix_issue(result):
                fixed_count += 1
        
        if fixed_count > 0:
            messagebox.showinfo("Auto-Fix Complete", 
                               f"Fixed {fixed_count} issues. Re-running health check...")
            self.show()  # Re-run check
        else:
            messagebox.showinfo("Auto-Fix Complete", 
                               "No issues could be automatically fixed.")