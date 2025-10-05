#!/usr/bin/env python3
"""
Setup script for private GitHub repository for personal Kodi builds
"""

import os
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def setup_private_repo():
    """Setup a private GitHub repository for personal builds"""
    print("🔐 Setting up Private GitHub Repository for Personal Builds")
    print("=" * 60)
    
    # Define paths
    home = Path.home()
    private_repo_path = home / "OneDrive" / "Documents" / "gusface-private"
    
    print(f"📁 Creating private repo at: {private_repo_path}")
    
    # Create directory structure
    private_repo_path.mkdir(parents=True, exist_ok=True)
    
    folders = [
        "personal_builds",
        "personal_wizard",
        "secure_configs"
    ]
    
    for folder in folders:
        (private_repo_path / folder).mkdir(exist_ok=True)
        print(f"   ✅ Created: {folder}/")
    
    # Create README for private repo
    readme_content = """# GUS Face - Private Kodi Repository

**⚠️ PRIVATE REPOSITORY - Contains Personal Data**

This repository contains:
- Personal Kodi builds with debrid service credentials
- Private wizard configurations
- Personal addon settings and sources

## Security Notes:
- Never make this repository public
- Only clone on trusted devices
- Contains Real-Debrid/AllDebrid credentials
- Keep access restricted to your accounts only

## Structure:
```
personal_builds/     - Full personal builds with credentials
personal_wizard/     - Wizard configs with personal data
secure_configs/      - Addon settings and sources
```

## Usage:
1. Clone this repo on new devices: `git clone https://github.com/YOURUSERNAME/gusface-private.git`
2. Use personal builds to setup Kodi with all your credentials
3. Update builds when you change your main setup

Created by: GUS Face Private Build System
"""
    
    readme_file = private_repo_path / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("   ✅ Created: README.md")
    
    # Create .gitignore for extra security
    gitignore_content = """# Extra security - ignore temp files that might contain sensitive data
*.tmp
*.temp
*.log
temp_*/
.DS_Store
Thumbs.db

# Backup files
*.bak
*.backup
"""
    
    gitignore_file = private_repo_path / ".gitignore"
    with open(gitignore_file, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("   ✅ Created: .gitignore")
    
    # Initialize git repo
    os.chdir(private_repo_path)
    
    success, output, error = run_command("git init")
    if success:
        print("   ✅ Initialized git repository")
    else:
        print(f"   ⚠️  Git init failed: {error}")
        return False
    
    # Add files
    run_command("git add .")
    run_command('git commit -m "Initial commit - Private Kodi repository setup"')
    
    print("\n🎯 Next Steps:")
    print("1. Create a private repository on GitHub named 'gusface-private'")
    print("2. Run these commands in the private repo folder:")
    print(f"   cd \"{private_repo_path}\"")
    print("   git remote add origin https://github.com/YOURUSERNAME/gusface-private.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("\n3. Update create_build.py to use this private repo:")
    
    # Create updated build script config
    config_content = f"""# Private Repository Configuration
PRIVATE_REPO_PATH = r"{private_repo_path}"
PRIVATE_BUILDS_DIR = PRIVATE_REPO_PATH / "personal_builds"
PRIVATE_WIZARD_DIR = PRIVATE_REPO_PATH / "personal_wizard"
"""
    
    config_file = private_repo_path.parent.parent / "Git_gusface" / "gusface.github.io" / "private_config.py"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"   ✅ Created config file: {config_file}")
    print("\n🔒 Your private repository is ready!")
    print(f"📍 Location: {private_repo_path}")
    
    return True

def main():
    """Main entry point"""
    try:
        setup_private_repo()
        print("\n🎉 Private repository setup completed successfully!")
    except Exception as e:
        print(f"\n❌ Error setting up private repository: {e}")

if __name__ == "__main__":
    main()