"""
Context-sensitive help system for GitHub Account Manager
"""
import tkinter as tk
from tkinter import ttk
import webbrowser
import os

class HelpSystem:
    """Context-sensitive help system"""
    
    HELP_TOPICS = {
        "ssh_key_generation": {
            "title": "SSH Key Generation",
            "content": """
SSH keys are used to authenticate with GitHub without passwords.

What we're doing:
1. Creating a unique Ed25519 key pair for your account
2. The private key stays on your computer (never share this!)
3. The public key gets added to GitHub
4. This allows secure, passwordless access to your repositories

Key Benefits:
• More secure than passwords
• No need to enter credentials repeatedly
• Works with Git commands automatically
• Can be revoked easily if compromised

Troubleshooting:
• If generation fails, ensure you have write access to ~/.ssh
• On Windows, make sure Git Bash is installed
• If you see permission errors, try running as administrator
• Make sure ssh-keygen is available in your PATH
            """,
            "links": [
                ("GitHub SSH Key Guide", "https://docs.github.com/en/authentication/connecting-to-github-with-ssh"),
                ("SSH Key Best Practices", "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-ssh-keys")
            ]
        },
        
        "github_setup": {
            "title": "Adding SSH Key to GitHub",
            "content": """
After generating your SSH key, you need to add the PUBLIC key to GitHub:

Step-by-step process:
1. Copy the public key (the app will help with this)
2. Go to GitHub.com and sign in
3. Click your profile picture → Settings
4. In the left sidebar, click "SSH and GPG keys"
5. Click "New SSH key" button
6. Give it a descriptive title (e.g., "My Laptop - Personal")
7. Paste the ENTIRE public key in the "Key" field
8. Click "Add SSH key"
9. You may need to confirm with your password

Testing the connection:
• Use the "Test Connection" button in this app
• Or manually run: ssh -T git@github.com-[account-name]
• You should see: "Hi [username]! You've successfully authenticated"

Important Notes:
• Only add the PUBLIC key (.pub file) to GitHub
• Never share your private key with anyone
• Each computer/account should have its own key pair
            """,
            "links": [
                ("Add SSH Key to GitHub", "https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account"),
                ("Test SSH Connection", "https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection")
            ]
        },
        
        "multiple_accounts": {
            "title": "Managing Multiple GitHub Accounts",
            "content": """
This app helps you manage multiple GitHub accounts on the same computer.

How it works:
• Each account gets its own SSH key
• SSH config uses different host aliases (github.com-personal, github.com-work)
• Git repositories are configured to use the correct account
• Remote URLs use the account-specific host alias

Example Setup:
• Personal account: git@github.com-personal:username/repo.git
• Work account: git@github.com-work:company/repo.git

Benefits:
• Separate commit histories for different contexts
• No more accidental commits with wrong account
• Easy switching between accounts per repository
• Secure isolation between personal and work projects

Common Use Cases:
• Personal projects vs. work projects
• Different organizations or clients
• Open source contributions vs. private work
• Testing with different GitHub accounts
            """,
            "links": [
                ("GitHub Multiple Accounts Guide", "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address")
            ]
        },
        
        "repository_configuration": {
            "title": "Repository Configuration",
            "content": """
Each Git repository needs to know which GitHub account to use.

What the app configures:
• Remote URL with account-specific host
• Git user.name and user.email for commits
• SSH key association through host alias

For new repositories:
1. Initialize with 'git init' or clone
2. Use "Configure New Project" in the app
3. Select the appropriate account
4. App sets up remote URL and Git config
5. Create repository on GitHub (manually or with token)
6. Push your first commit

For existing repositories:
1. Use "Switch Account" feature
2. App updates remote URL and Git config
3. Future commits will use the new account

Remote URL Format:
• Standard: git@github.com:username/repo.git
• Multi-account: git@github.com-accountname:username/repo.git

Git Configuration per Repo:
• user.name = Account display name
• user.email = Account email address
• remote.origin.url = Account-specific SSH URL
            """,
            "links": [
                ("Git Configuration", "https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup"),
                ("Git Remotes", "https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes")
            ]
        },
        
        "troubleshooting": {
            "title": "Common Issues and Solutions",
            "content": """
Here are solutions to common problems:

🔑 SSH Key Issues:
• "Permission denied (publickey)" → Key not added to GitHub or SSH agent
• "Bad permissions" → Run: chmod 600 ~/.ssh/id_* (Unix/Mac)
• "No such file" → Generate new SSH key or check path

🔧 Configuration Issues:
• Wrong commit author → Check git config user.email in repository
• "Remote not found" → Verify repository exists on GitHub
• "Access denied" → Check if SSH key matches GitHub account

🌐 Connection Issues:
• "Connection timeout" → Check internet connection and firewall
• "Host key verification failed" → Run: ssh-keyscan github.com >> ~/.ssh/known_hosts
• "Agent has no identities" → Run: ssh-add ~/.ssh/keyname

📁 Repository Issues:
• "Not a git repository" → Run: git init in the project folder
• "Remote already exists" → Use "Switch Account" instead of "Configure New"
• "Repository not found" → Check repository name and permissions

🛠️ Quick Fixes:
• Restart SSH agent: eval "$(ssh-agent -s)" && ssh-add ~/.ssh/keyname
• Clear SSH connections: ssh -O exit git@github.com
• Reset Git config: git config --unset user.email && git config --unset user.name
• Test SSH: ssh -T git@github.com-accountname
            """,
            "links": [
                ("GitHub SSH Troubleshooting", "https://docs.github.com/en/authentication/troubleshooting-ssh"),
                ("Git Troubleshooting", "https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository")
            ]
        }
    }
    
    @staticmethod
    def show_help(parent, topic: str):
        """Show help dialog for specific topic"""
        if topic not in HelpSystem.HELP_TOPICS:
            HelpSystem.show_general_help(parent)
            return
        
        help_info = HelpSystem.HELP_TOPICS[topic]
        
        help_window = tk.Toplevel(parent)
        help_window.title(f"Help: {help_info['title']}")
        help_window.geometry("600x500")
        help_window.transient(parent)
        
        # Main content
        main_frame = ttk.Frame(help_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=help_info['title'], 
                               font=('Arial', 16, 'bold'))
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Content area with scrollbar
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        text_widget = tk.Text(content_frame, wrap=tk.WORD, padx=10, pady=10,
                             font=('Arial', 10), bg='#f8f9fa', relief='flat')
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        text_widget.insert('1.0', help_info['content'].strip())
        text_widget.config(state='disabled')
        
        # Links section
        if 'links' in help_info and help_info['links']:
            links_frame = ttk.LabelFrame(main_frame, text="Helpful Links")
            links_frame.pack(fill='x', pady=(10, 0))
            
            for link_text, link_url in help_info['links']:
                link_button = ttk.Button(links_frame, text=f"🔗 {link_text}",
                                       command=lambda url=link_url: webbrowser.open(url))
                link_button.pack(anchor='w', padx=5, pady=2)
        
        # Close button
        button_frame = ttk.Frame(help_window)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Close", 
                  command=help_window.destroy).pack(side='right', padx=10)
    
    @staticmethod
    def show_general_help(parent):
        """Show general help overview"""
        help_window = tk.Toplevel(parent)
        help_window.title("GitHub Account Manager Help")
        help_window.geometry("500x400")
        help_window.transient(parent)
        
        main_frame = ttk.Frame(help_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="GitHub Account Manager Help", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        help_topics = [
            ("🔑 SSH Key Generation", "ssh_key_generation"),
            ("🔧 GitHub Setup", "github_setup"),
            ("👥 Multiple Accounts", "multiple_accounts"),
            ("📁 Repository Configuration", "repository_configuration"),
            ("🛠️ Troubleshooting", "troubleshooting")
        ]
        
        for topic_name, topic_key in help_topics:
            btn = ttk.Button(main_frame, text=topic_name,
                           command=lambda k=topic_key: [help_window.destroy(), 
                                                       HelpSystem.show_help(parent, k)])
            btn.pack(fill='x', pady=2)
        
        # Quick links
        links_frame = ttk.LabelFrame(main_frame, text="Quick Actions")
        links_frame.pack(fill='x', pady=(20, 0))
        
        def open_github_keys():
            webbrowser.open("https://github.com/settings/keys")
        
        def open_ssh_folder():
            ssh_dir = os.path.expanduser("~/.ssh")
            if os.path.exists(ssh_dir):
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(ssh_dir)
                    elif os.name == 'posix':  # macOS/Linux
                        os.system(f'open "{ssh_dir}"' if os.uname().sysname == 'Darwin' 
                                else f'xdg-open "{ssh_dir}"')
                except:
                    pass
        
        ttk.Button(links_frame, text="🔗 Open GitHub SSH Settings",
                  command=open_github_keys).pack(fill='x', pady=2)
        ttk.Button(links_frame, text="📁 Open SSH Folder",
                  command=open_ssh_folder).pack(fill='x', pady=2)
        
        ttk.Button(help_window, text="Close", 
                  command=help_window.destroy).pack(pady=10)

class QuickStartGuide:
    """Quick start guide for new users"""
    
    @staticmethod
    def show(parent):
        """Show quick start guide"""
        guide_window = tk.Toplevel(parent)
        guide_window.title("Quick Start Guide")
        guide_window.geometry("600x500")
        guide_window.transient(parent)
        guide_window.grab_set()
        
        # Create notebook for steps
        notebook = ttk.Notebook(guide_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        steps = [
            ("1. Setup", QuickStartGuide.create_setup_step),
            ("2. Create Account", QuickStartGuide.create_account_step),
            ("3. Configure Repo", QuickStartGuide.create_repo_step),
            ("4. Test & Use", QuickStartGuide.create_test_step)
        ]
        
        for step_name, step_creator in steps:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=step_name)
            step_creator(frame)
        
        # Navigation buttons
        nav_frame = ttk.Frame(guide_window)
        nav_frame.pack(fill='x', pady=10)
        
        def next_step():
            current = notebook.index(notebook.select())
            if current < len(steps) - 1:
                notebook.select(current + 1)
        
        def prev_step():
            current = notebook.index(notebook.select())
            if current > 0:
                notebook.select(current - 1)
        
        ttk.Button(nav_frame, text="← Previous", command=prev_step).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Next →", command=next_step).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Close", command=guide_window.destroy).pack(side='right', padx=5)
    
    @staticmethod
    def create_setup_step(parent):
        """Create setup step content"""
        content = """
Welcome to GitHub Account Manager!

This tool helps you manage multiple GitHub accounts on one computer.

Before we start, make sure you have:
✓ Git installed on your system
✓ At least one GitHub account
✓ Internet connection

What we'll do:
1. Create an SSH key for secure authentication
2. Add the public key to your GitHub account
3. Configure a repository to use the account
4. Test the setup

This process takes about 5-10 minutes per account.

Ready? Click "Next" to continue!
        """
        
        text_widget = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20,
                             font=('Arial', 11), bg='#f8f9fa', relief='flat')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', content.strip())
        text_widget.config(state='disabled')
    
    @staticmethod
    def create_account_step(parent):
        """Create account setup step content"""
        content = """
Step 2: Create Your First Account

1. Go to the "Accounts" tab in the main application
2. Click "+ Add Account"
3. Fill in the details:
   • Account Name: A nickname (e.g., "personal", "work")
   • Email: Your GitHub email address
   • GitHub Username: Your GitHub username

4. Click "Create Account"
5. The app will generate an SSH key automatically
6. Follow the instructions to add the public key to GitHub

Tips:
• Use descriptive account names like "john-personal" or "jane-work"
• Make sure the email matches your GitHub account
• The SSH key will be saved in ~/.ssh/[account-name]

After creating the account, test the connection using the "Test Connection" button.
        """
        
        text_widget = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20,
                             font=('Arial', 11), bg='#f8f9fa', relief='flat')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', content.strip())
        text_widget.config(state='disabled')
    
    @staticmethod
    def create_repo_step(parent):
        """Create repository configuration step content"""
        content = """
Step 3: Configure a Repository

Option A - New Repository:
1. Create a new folder for your project
2. Run "git init" in the folder (or let your IDE do it)
3. Go to "Repositories" tab and scan the parent folder
4. Select the repository and click "Configure New Project"
5. Choose your account and repository details
6. The app will set up the remote URL and Git config

Option B - Existing Repository:
1. Go to "Repositories" tab and scan your projects folder
2. Find repositories that need account switching
3. Select a repository and choose an account
4. Click "Switch Account"
5. The app will update the remote URL and Git config

The app handles:
• Setting the correct remote URL format
• Configuring Git user name and email
• Creating the repository on GitHub (if you provide a token)
        """
        
        text_widget = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20,
                             font=('Arial', 11), bg='#f8f9fa', relief='flat')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', content.strip())
        text_widget.config(state='disabled')
    
    @staticmethod
    def create_test_step(parent):
        """Create testing step content"""
        content = """
Step 4: Test and Use Your Setup

Testing:
1. Use "Test Connection" in the Accounts tab
2. Try pushing a commit to a configured repository
3. Check that commits show the correct author

Daily Usage:
• The app remembers your last scanned folder
• Use "Refresh" to update repository status
• Switch accounts per repository as needed
• Create backups before major changes

Troubleshooting:
• Use "Settings" → "Run Health Check" to diagnose issues
• The Recovery Wizard can fix common problems
• Export debug info if you need help

Best Practices:
• Keep the app configuration backed up
• Test SSH connections regularly
• Use descriptive commit messages
• Keep personal and work projects in separate folders

You're all set! Happy coding! 🎉

Need help? Use the "Information" button or check the help topics.
        """
        
        text_widget = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20,
                             font=('Arial', 11), bg='#f8f9fa', relief='flat')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', content.strip())
        text_widget.config(state='disabled')