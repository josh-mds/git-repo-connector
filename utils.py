"""
Utility functions for GitHub Account Manager
"""
import os
import re
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from git import Repo

class GitUtils:
    """Git-related utility functions"""
    
    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Check if path is a Git repository"""
        try:
            Repo(path)
            return True
        except:
            return False
    
    @staticmethod
    def get_repo_info(repo_path: str) -> Dict:
        """Get detailed repository information"""
        try:
            repo = Repo(repo_path)
            
            # Get remote info
            remote_url = None
            if 'origin' in repo.remotes:
                remote_url = repo.remotes.origin.url
            
            # Get current branch
            try:
                current_branch = repo.active_branch.name
            except:
                current_branch = "detached HEAD"
            
            # Get last commit info
            try:
                last_commit = repo.head.commit
                last_author = last_commit.author.name
                last_email = last_commit.author.email
                last_message = last_commit.message.strip()
                last_date = last_commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
            except:
                last_author = last_email = last_message = last_date = "Unknown"
            
            # Get repository status
            status = "Clean"
            if repo.is_dirty():
                status = "Modified"
            elif repo.untracked_files:
                status = "Untracked files"
            
            # Get configured user
            try:
                config_name = repo.config_reader().get_value("user", "name", "")
                config_email = repo.config_reader().get_value("user", "email", "")
            except:
                config_name = config_email = ""
            
            return {
                "path": repo_path,
                "remote_url": remote_url,
                "current_branch": current_branch,
                "status": status,
                "last_commit": {
                    "author": last_author,
                    "email": last_email,
                    "message": last_message,
                    "date": last_date
                },
                "config": {
                    "name": config_name,
                    "email": config_email
                }
            }
        except Exception as e:
            return {"path": repo_path, "error": str(e)}
    
    @staticmethod
    def configure_repo_user(repo_path: str, name: str, email: str) -> bool:
        """Configure Git user for repository"""
        try:
            repo = Repo(repo_path)
            with repo.config_writer() as config:
                config.set_value("user", "name", name)
                config.set_value("user", "email", email)
            return True
        except Exception:
            return False
    
    @staticmethod
    def set_remote_url(repo_path: str, remote_name: str, url: str) -> bool:
        """Set remote URL for repository"""
        try:
            repo = Repo(repo_path)
            if remote_name in repo.remotes:
                repo.remotes[remote_name].set_url(url)
            else:
                repo.create_remote(remote_name, url)
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract_repo_info_from_url(url: str) -> Optional[Dict]:
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

class SSHUtils:
    """SSH-related utility functions"""
    
    @staticmethod
    def get_ssh_dir() -> str:
        """Get SSH directory path"""
        return os.path.expanduser("~/.ssh")
    
    @staticmethod
    def get_ssh_config_path() -> str:
        """Get SSH config file path"""
        return os.path.join(SSHUtils.get_ssh_dir(), "config")
    
    @staticmethod
    def ensure_ssh_dir() -> bool:
        """Ensure SSH directory exists with correct permissions"""
        try:
            ssh_dir = SSHUtils.get_ssh_dir()
            os.makedirs(ssh_dir, exist_ok=True)
            
            # Set correct permissions on Unix-like systems
            if os.name != 'nt':
                os.chmod(ssh_dir, 0o700)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_ssh_key(key_path: str, email: str, passphrase: str = "") -> bool:
        """Generate SSH key pair"""
        try:
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", email,
                "-f", key_path,
                "-N", passphrase
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Set correct permissions on private key (Unix-like systems)
            if os.name != 'nt':
                os.chmod(key_path, 0o600)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def add_key_to_agent(key_path: str) -> bool:
        """Add SSH key to SSH agent"""
        try:
            # Start SSH agent if needed (Windows)
            if platform.system() == "Windows":
                subprocess.run(["powershell", "-Command", "Start-Service ssh-agent"], 
                             check=False, capture_output=True)
            
            # Add key to agent
            subprocess.run(["ssh-add", key_path], check=True, capture_output=True, text=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def test_ssh_connection(host: str, timeout: int = 10) -> Tuple[bool, str]:
        """Test SSH connection to GitHub"""
        try:
            cmd = ["ssh", "-T", f"git@{host}", "-o", f"ConnectTimeout={timeout}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
            
            # GitHub SSH returns exit code 1 on successful auth
            if "successfully authenticated" in result.stderr:
                return True, "Connection successful"
            else:
                return False, result.stderr or "Connection failed"
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def read_public_key(key_path: str) -> Optional[str]:
        """Read public key content"""
        try:
            pub_key_path = f"{key_path}.pub"
            with open(pub_key_path, 'r') as f:
                return f.read().strip()
        except Exception:
            return None
    
    @staticmethod
    def is_key_in_agent(key_path: str) -> bool:
        """Check if SSH key is loaded in SSH agent"""
        try:
            result = subprocess.run(["ssh-add", "-l"], capture_output=True, text=True)
            return key_path in result.stdout
        except:
            return False

class FileUtils:
    """File system utility functions"""
    
    @staticmethod
    def safe_filename(name: str) -> str:
        """Create safe filename from string"""
        # Replace invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove excessive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        # Trim underscores from ends
        return safe_name.strip('_')
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensure directory exists"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def copy_file_safely(src: str, dst: str) -> bool:
        """Copy file with error handling"""
        try:
            import shutil
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def backup_file(file_path: str) -> Optional[str]:
        """Create backup of file with timestamp"""
        if not os.path.exists(file_path):
            return None
        
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            if FileUtils.copy_file_safely(file_path, backup_path):
                return backup_path
        except Exception:
            pass
        
        return None

class GitHubUtils:
    """GitHub API utility functions"""
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate GitHub username format"""
        pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
        return re.match(pattern, username) is not None
    
    @staticmethod
    def create_repository(owner: str, repo_name: str, token: str, private: bool = False) -> Tuple[bool, str]:
        """Create GitHub repository using API"""
        if not token:
            return False, "GitHub token required"
        
        try:
            import requests
            
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
                return False, f"Failed to create repository: {error_msg}"
        
        except Exception as e:
            return False, f"Error creating repository: {str(e)}"
    
    @staticmethod
    def check_repository_exists(owner: str, repo_name: str, token: str = None) -> Tuple[bool, bool]:
        """Check if GitHub repository exists"""
        try:
            import requests
            
            url = f"https://api.github.com/repos/{owner}/{repo_name}"
            headers = {}
            
            if token:
                headers["Authorization"] = f"token {token}"
            
            response = requests.get(url, headers=headers)
            return True, response.status_code == 200
        
        except Exception:
            return False, False

class ConfigUtils:
    """Configuration utility functions"""
    
    @staticmethod
    def load_json_config(file_path: str) -> Dict:
        """Load JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    @staticmethod
    def save_json_config(file_path: str, config: Dict) -> bool:
        """Save JSON configuration file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
        """Merge two configuration dictionaries"""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = ConfigUtils.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged

class SystemUtils:
    """System-related utility functions"""
    
    @staticmethod
    def get_platform_info() -> Dict:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version()
        }
    
    @staticmethod
    def is_command_available(command: str) -> bool:
        """Check if command is available in PATH"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, text=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def open_file_manager(path: str) -> bool:
        """Open file manager at specified path"""
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux and others
                subprocess.run(["xdg-open", path])
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_home_directory() -> str:
        """Get user home directory"""
        return str(Path.home())

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_repo_name(name: str) -> bool:
        """Validate repository name format"""
        if not name or len(name) > 100:
            return False
        
        # GitHub repository name rules
        pattern = r'^[a-zA-Z0-9._-]+$'
        return re.match(pattern, name) is not None
    
    @staticmethod
    def validate_account_name(name: str) -> bool:
        """Validate account name format"""
        if not name or len(name) > 50:
            return False
        
        pattern = r'^[a-zA-Z0-9\-_]+$'
        return re.match(pattern, name) is not None
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 100) -> str:
        """Sanitize user input"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>&"\'`]', '', text)
        # Limit length
        sanitized = sanitized[:max_length]
        # Strip whitespace
        return sanitized.strip()