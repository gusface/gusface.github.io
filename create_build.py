#!/usr/bin/env python3
"""
Kodi Build Creator Script
Creates a build ZIP from repo addons folder and current Kodi configuration
"""

import os
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path

class KodiBuildCreator:
    def __init__(self, build_type="public"):
        # Paths
        self.script_dir = Path(__file__).parent
        self.repo_addons_dir = self.script_dir / "addons"
        self.kodi_userdata = Path(os.path.expandvars(r"%APPDATA%\Kodi\userdata"))
        
        # Build type determines privacy level
        self.build_type = build_type  # "public" or "personal"
        
        # Build info
        self.build_name = "GUSBuild"
        self.build_version = "1.0"
        
        # Set output directories based on build type
        if self.build_type == "personal":
            # Personal builds go to a private local folder
            self.builds_dir = Path.home() / "Documents" / "Private_Kodi_Builds"
            self.build_name += "_Personal"
        else:
            # Public builds go to the repo builds folder
            self.builds_dir = self.script_dir / "builds"
            self.build_name += "_Public"
        
        # Create builds directory
        self.builds_dir.mkdir(exist_ok=True)
        
        print(f"🏷️  Build Type: {self.build_type.upper()}")
        print(f"📁 Output Directory: {self.builds_dir}")
        
    def get_build_filename(self):
        """Generate build filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{self.build_name}_v{self.build_version}_{timestamp}.zip"
    
    def validate_kodi_path(self):
        """Check if Kodi userdata exists"""
        if not self.kodi_userdata.exists():
            print(f"❌ Kodi userdata not found at: {self.kodi_userdata}")
            print("Please ensure Kodi is installed and has been run at least once.")
            return False
        print(f"✅ Found Kodi userdata at: {self.kodi_userdata}")
        return True
    
    def clean_sensitive_data(self, temp_dir):
        """Remove sensitive/personal data from build"""
        if self.build_type == "personal":
            print("🔒 Personal build - Keeping all data intact (including debrid info)")
            return  # Skip all cleaning for personal builds
        
        print("🧹 Cleaning sensitive data for public build...")
        
        # Remove entire directories
        sensitive_dirs = [
            "Thumbnails",
            "Database",  # Remove all databases to prevent personal history
            "temp",
            "cache",
        ]
        
        for dirname in sensitive_dirs:
            dir_path = temp_dir / dirname
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
                print(f"   ❌ Removed directory: {dirname}")
        
        # Clean debrid and personal data from addon_data
        self.clean_addon_data(temp_dir)
        
        # Clean personal info from XML files
        self.clean_xml_files(temp_dir)
    
    def clean_addon_data(self, temp_dir):
        """Clean sensitive data from addon_data folders"""
        print("🔒 Cleaning addon data...")
        
        addon_data_dir = temp_dir / "addon_data"
        if not addon_data_dir.exists():
            return
        
        # Debrid services and sensitive addons
        sensitive_addons = [
            # Debrid services
            "*debrid*",
            "*realdebrid*", 
            "*alldebrid*",
            "*premiumize*",
            "*torbox*",
            
            # Torrent/streaming that might have personal data
            "*torrent*",
            "*seedbox*",
            
            # Cloud services with personal data
            "*drive*",
            "*dropbox*",
            "*onedrive*",
            
            # VPN services
            "*vpn*",
            
            # Login-based services
            "*netflix*",
            "*hulu*",
            "*amazon*",
            "*disney*",
        ]
        
        for pattern in sensitive_addons:
            for addon_dir in addon_data_dir.glob(pattern):
                if addon_dir.is_dir():
                    # Instead of deleting, clean the settings files
                    self.clean_addon_settings(addon_dir)
                    print(f"   🧹 Cleaned settings: {addon_dir.name}")
    
    def clean_addon_settings(self, addon_dir):
        """Clean sensitive settings from a specific addon"""
        settings_file = addon_dir / "settings.xml"
        if settings_file.exists():
            try:
                # Read the file
                with open(settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove common sensitive patterns
                sensitive_patterns = [
                    r'<setting id="[^"]*(?:username|user|login|email)"[^>]*value="[^"]+"',
                    r'<setting id="[^"]*(?:password|pass|token|key|secret)"[^>]*value="[^"]+"',
                    r'<setting id="[^"]*(?:api|auth)"[^>]*value="[^"]+"',
                ]
                
                import re
                for pattern in sensitive_patterns:
                    content = re.sub(pattern, lambda m: m.group(0).split('value="')[0] + 'value=""', content)
                
                # Write cleaned content back
                with open(settings_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"     ⚠️  Warning: Could not clean {settings_file.name}: {e}")
    
    def clean_xml_files(self, temp_dir):
        """Clean personal data from main XML files"""
        print("📝 Cleaning XML files...")
        
        # Clean sources.xml
        sources_file = temp_dir / "sources.xml"
        if sources_file.exists():
            self.clean_sources_xml(sources_file)
        
        # Clean favourites.xml
        favourites_file = temp_dir / "favourites.xml"
        if favourites_file.exists():
            self.clean_favourites_xml(favourites_file)
    
    def clean_sources_xml(self, sources_file):
        """Remove personal sources from sources.xml"""
        try:
            with open(sources_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove paths that might be personal
            import re
            # Remove local file paths
            content = re.sub(r'<path>[A-Z]:[^<]*</path>', '<path></path>', content)
            # Remove UNC paths
            content = re.sub(r'<path>\\\\[^<]*</path>', '<path></path>', content)
            # Remove personal network paths
            content = re.sub(r'<path>[^<]*@[^<]*</path>', '<path></path>', content)
            
            with open(sources_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print("   ✅ Cleaned sources.xml")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not clean sources.xml: {e}")
    
    def clean_favourites_xml(self, favourites_file):
        """Clean personal favourites"""
        try:
            # For now, just remove the whole file as favourites are often personal
            favourites_file.unlink()
            print("   ✅ Removed personal favourites.xml")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not clean favourites.xml: {e}")
    
    def copy_kodi_settings(self, temp_dir):
        """Copy Kodi settings and configuration"""
        print("📋 Copying Kodi settings...")
        
        # Essential files for build
        essential_files = [
            "guisettings.xml",      # UI/Theme settings
            "sources.xml",          # Media sources
            "favourites.xml",       # User favorites
            "advancedsettings.xml", # Advanced Kodi settings
            "playercorefactory.xml", # Player settings
        ]
        
        # Essential directories
        essential_dirs = [
            "addon_data",           # Addon configurations
            "keymaps",             # Custom keymaps
            "Database",            # Kodi databases (will be cleaned)
        ]
        
        # Copy files
        for filename in essential_files:
            src = self.kodi_userdata / filename
            if src.exists():
                shutil.copy2(src, temp_dir / filename)
                print(f"   ✅ Copied: {filename}")
            else:
                print(f"   ⚠️  Not found: {filename}")
        
        # Copy directories
        for dirname in essential_dirs:
            src = self.kodi_userdata / dirname
            dst = temp_dir / dirname
            if src.exists():
                shutil.copytree(src, dst, ignore_errors=True)
                print(f"   ✅ Copied directory: {dirname}")
            else:
                print(f"   ⚠️  Directory not found: {dirname}")
    
    def copy_kodi_addons(self, temp_dir):
        """Copy addons directly from Kodi installation"""
        print("📦 Copying addons from Kodi installation...")
        
        kodi_addons = self.kodi_userdata / "addons"
        addons_dst = temp_dir / "addons"
        addons_dst.mkdir(exist_ok=True)
        
        if not kodi_addons.exists():
            print("   ⚠️  No addons found in Kodi installation")
            return
        
        # Copy all addon folders from Kodi
        addon_count = 0
        for addon_dir in kodi_addons.iterdir():
            if addon_dir.is_dir() and not addon_dir.name.startswith('.'):
                dst = addons_dst / addon_dir.name
                shutil.copytree(addon_dir, dst, ignore_errors=True)
                print(f"   ✅ Copied addon: {addon_dir.name}")
                addon_count += 1
        
        print(f"   📊 Total addons copied: {addon_count}")
    
    def create_build_info(self, temp_dir):
        """Create build info file"""
        build_info = {
            "name": self.build_name,
            "version": self.build_version,
            "created": datetime.now().isoformat(),
            "creator": "GUS Face Repository",
            "description": "Custom Kodi build with curated addons and theme"
        }
        
        info_file = temp_dir / "build_info.json"
        with open(info_file, 'w') as f:
            json.dump(build_info, f, indent=2)
        
        print(f"   ✅ Created build info file")
    
    def create_zip(self, temp_dir, zip_filename):
        """Create the final build ZIP"""
        zip_path = self.builds_dir / zip_filename
        
        print(f"📦 Creating build ZIP: {zip_filename}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    # Create relative path for ZIP
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        # Get ZIP size
        zip_size = zip_path.stat().st_size
        zip_size_mb = zip_size / (1024 * 1024)
        
        print(f"✅ Build created successfully!")
        print(f"   File: {zip_path}")
        print(f"   Size: {zip_size_mb:.1f} MB")
        
        return zip_path
    
    def create_build(self):
        """Main function to create the build"""
        print("🚀 Starting Kodi Build Creation...")
        print("=" * 50)
        
        # Validate Kodi installation
        if not self.validate_kodi_path():
            return False
        
        # Create temporary directory
        temp_dir = Path("temp_build")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        try:
            # Copy Kodi settings and configuration
            self.copy_kodi_settings(temp_dir)
            
            # Copy addons directly from Kodi
            self.copy_kodi_addons(temp_dir)
            
            # Clean sensitive data
            self.clean_sensitive_data(temp_dir)
            
            # Create build info
            self.create_build_info(temp_dir)
            
            # Create ZIP file
            zip_filename = self.get_build_filename()
            zip_path = self.create_zip(temp_dir, zip_filename)
            
            print("\n🎉 Build creation completed successfully!")
            print(f"Your build is ready at: {zip_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating build: {str(e)}")
            return False
            
        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main entry point"""
    import sys
    
    # Check command line arguments
    build_type = "public"  # Default
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["personal", "private", "p"]:
            build_type = "personal"
        elif sys.argv[1].lower() in ["public", "pub", "clean"]:
            build_type = "public"
        else:
            print("🔄 Usage: python create_build.py [personal|public]")
            print("   personal = Full build with your debrid info (saved locally)")
            print("   public   = Clean build for sharing (saved to repo)")
            return
    
    print("\n" + "=" * 60)
    print(f"🚀 KODI BUILD CREATOR - {build_type.upper()} MODE")
    print("=" * 60)
    
    creator = KodiBuildCreator(build_type)
    success = creator.create_build()
    
    if success:
        print("\n📝 Next steps:")
        if build_type == "personal":
            print("1. Use this build to setup your own devices")
            print("2. Keep this file private - it contains your personal data")
            print("3. Consider creating a public build for sharing")
        else:
            print("1. Test the build on a clean Kodi installation")
            print("2. Add the ZIP to your repository")
            print("3. Update addons.xml with build information")
    else:
        print("\n❌ Build creation failed. Please check the errors above.")

if __name__ == "__main__":
    main()