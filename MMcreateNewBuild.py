#!/usr/bin/env python3
"""
make_kodi_build.py
Creates a zipped Kodi build from your current Kodi userdata/addons while excluding caches/logs.

This script is designed for creators who want to package their Kodi configuration 
(settings and installed addons) into a single, clean ZIP file for use with a 
Kodi wizard or build repository.

Usage:
  # Basic usage (output to default OneDrive folder)
  python make_kodi_build.py

  # Specific usage (override default paths)
  python make_kodi_build.py --kodi "C:/Users/Mark/AppData/Roaming/Kodi" --out "D:/custom/output/folder"
"""

import os
import sys
import zipfile
import argparse
from pathlib import Path
from datetime import datetime
import fnmatch

# -------------------------
def get_default_kodi_path():
    """
    Safely determines the default Kodi path in an OS-agnostic way 
    to prevent unicodeescape errors on Windows/WSL.
    """
    # Use environment variables and Path objects for safe construction
    if sys.platform == "win32" or "APPDATA" in os.environ:
        # Windows default path: %APPDATA%/Kodi
        return Path(os.path.expandvars("%APPDATA%")) / "Kodi"
    elif sys.platform.startswith('linux'):
        # Linux/LibreELEC default path
        return Path.home() / ".kodi"
    elif sys.platform == "darwin":
        # macOS default path
        return Path.home() / "Library" / "Application Support" / "Kodi"
    else:
        # Fallback to a common default or current directory
        return Path.home() / ".kodi"

def parse_args():
    """Parses command-line arguments for the script."""
    
    # NEW DEFAULT OUTPUT PATH: User's specified OneDrive folder
    # Using a raw string and Path() to correctly handle the Windows path.
    default_out_path = Path(r"C:\Users\mrkme\OneDrive\Documents\Private_Kodi_Builds")
    
    p = argparse.ArgumentParser(description="Package Kodi folder into a build .zip")
    
    # Set the default Kodi path using the safe function
    default_kodi_path = get_default_kodi_path()
    
    p.add_argument("--kodi", 
                   default=str(default_kodi_path),
                   help=f"Path to your Kodi folder (default: {default_kodi_path})")
                   
    p.add_argument("--out", 
                   default=str(default_out_path),
                   help=f"Output folder for the build zip (default: {default_out_path})")
    p.add_argument("--name", 
                   default="GusFace_Build", 
                   help="Base name for the build zip (e.g., 'GusFace_Build_20240101_120000.zip')")
    p.add_argument("--dry-run", 
                   action="store_true", 
                   help="List files that WOULD be included, don't create zip")
    p.add_argument("--skip-large", 
                   type=int, 
                   default=95*1024*1024,
                   help="Skip files larger than this many bytes (default: 95MB). Set 0 to disable.")
    return p.parse_args()

# -------------------------
# Patterns for files and directories that should NEVER be included in a distribution build
EXCLUDE_PATTERNS = [
    # Addon installation files (packages) - downloaded by Kodi, not needed in build
    "addons/packages/*",
    # Local texture cache - huge and machine-specific
    "userdata/Thumbnails/*",
    "userdata/Database/Textures13.db",
    # Temporary files
    "temp/*",
    "cache/*",
    "logs/*",
    # General file exclusions
    "*.log",
    "*.cache",
    "kodi.old.log", # Explicitly exclude common log file
]

def should_exclude(rel_posix):
    """
    Checks if a relative file path (POSIX-style, e.g., 'userdata/settings.xml') 
    matches any of the global exclusion patterns using shell-style wildcard matching.
    """
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_posix, pattern):
            return True
    return False

# -------------------------
def make_build(args):
    """Main logic to create the Kodi build zip."""
    kodi_path = Path(args.kodi)
    if not kodi_path.is_dir():
        print(f"Error: Kodi path not found at {kodi_path}")
        print("Please ensure Kodi is installed or provide the correct path using --kodi.")
        sys.exit(1)
        
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{args.name}_{timestamp}.zip"
    zip_path = out_dir / zip_filename
    
    print("-" * 50)
    print(f"Kodi Source: {kodi_path}")
    print(f"Output Path: {zip_path} {'(DRY-RUN)' if args.dry_run else ''}")
    print(f"Max File Size: {args.skip_large / (1024*1024):.1f} MB (Set --skip-large 0 to disable)")
    print("-" * 50)
    
    included_files = []
    
    # Use ZipFile context manager unless it's a dry run
    zip_file = None
    if not args.dry_run:
        zip_file = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)

    try:
        # Walk through the Kodi directory
        for root, dirs, files in os.walk(kodi_path):
            current_dir = Path(root)
            
            # Paths to check for exclusion are relative to the Kodi folder, 
            # and must be POSIX-style (forward slashes) for pattern matching
            try:
                rel_path = current_dir.relative_to(kodi_path).as_posix()
            except ValueError:
                # Should not happen if kodi_path is the root, but good for safety
                continue

            # --- Pruning Top-Level Directories ---
            if rel_path == '.':
                # Only iterate into 'userdata' and 'addons' from the root.
                # Remove common excluded directories from being traversed at all.
                dirs_to_keep = ['userdata', 'addons']
                # Modify dirs in-place to affect os.walk traversal
                dirs[:] = [d for d in dirs if d in dirs_to_keep]
                
                # Skip files directly in the root (e.g., kodi.log, which is already excluded)
                files = [] 
                continue # Move to the next iteration (first child dir)

            # --- File Inclusion/Exclusion Logic ---
            for filename in files:
                file_path = current_dir / filename
                rel_file_path = file_path.relative_to(kodi_path).as_posix()
                
                # 1. Check exclusion patterns
                if should_exclude(rel_file_path):
                    continue
                
                # 2. Check for large files exclusion
                try:
                    file_size = file_path.stat().st_size
                    if args.skip_large > 0 and file_size > args.skip_large:
                        # Log large file skip only during dry run or if not dry run
                        if args.dry_run:
                            print(f"  [Skipped Large] {rel_file_path} ({file_size / (1024*1024):.2f} MB)")
                        continue
                except OSError:
                    # Ignore files that can't be stat-ed (e.g., permissions or broken symlinks)
                    continue
                
                # --- Add File to Archive / Dry Run List ---
                included_files.append(rel_file_path)
                
                if not args.dry_run:
                    # The archive path is the same as the relative path
                    zip_file.write(file_path, rel_file_path)

        # --- Final Output ---
        print("-" * 50)
        print(f"Total files to be included: {len(included_files)}")
        
        if args.dry_run:
            print("\n--- Files that would be included (Dry Run): ---")
            for f in included_files:
                print(f"  {f}")
            print("--- Dry Run Complete. No zip created. ---")
        else:
            print(f"\nSuccessfully created build: {zip_path}")
            
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        # Clean up the zip file if it was partially created
        if zip_file:
            zip_file.close()
        if not args.dry_run and zip_path.exists():
            print("Deleting incomplete zip file due to error.")
            zip_path.unlink() 
            
    finally:
        if zip_file:
            # Ensure the file is closed at the end of the operation
            zip_file.close()

if __name__ == "__main__":
    make_build(parse_args())
