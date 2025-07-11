#!/usr/bin/env python3
"""
Simple script to install pip in environments where it's not available
"""

import os
import sys
import urllib.request
import subprocess

def download_get_pip():
    """Download get-pip.py script"""
    url = "https://bootstrap.pypa.io/get-pip.py"
    print(f"Downloading pip installer from {url}...")
    
    try:
        urllib.request.urlretrieve(url, "get-pip.py")
        print("Download complete!")
        return True
    except Exception as e:
        print(f"Error downloading: {e}")
        return False

def install_pip():
    """Install pip using get-pip.py"""
    print("Installing pip...")
    
    try:
        # Install pip for user
        result = subprocess.run([sys.executable, "get-pip.py", "--user"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("pip installed successfully!")
            print("\nIMPORTANT: Add the following to your PATH:")
            print(f"export PATH=$PATH:~/.local/bin")
            print("\nOr add it permanently to ~/.bashrc:")
            print(f"echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc")
            print("source ~/.bashrc")
            return True
        else:
            print(f"Error installing pip: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists("get-pip.py"):
            os.remove("get-pip.py")

def main():
    print("=== Pip Installation Script ===\n")
    
    # Check if pip is already installed
    try:
        import pip
        print("pip is already installed!")
        print(f"Version: {pip.__version__}")
        return
    except ImportError:
        print("pip not found. Installing...")
    
    if download_get_pip() and install_pip():
        print("\n✓ Installation complete!")
        print("\nNext steps:")
        print("1. Update your PATH as shown above")
        print("2. Open a new terminal or run: source ~/.bashrc")
        print("3. Run: pip --version")
    else:
        print("\n✗ Installation failed!")
        print("Please try installing pip manually using your system's package manager")

if __name__ == "__main__":
    main()