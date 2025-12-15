#!/usr/bin/env python3
"""
setup_venv.py - Cross-platform virtual environment setup

Works on Linux, macOS, and Windows. Run with:
    python3 setup_venv.py

Or if python3 isn't available:
    python setup_venv.py
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("=" * 50)
    print("GoPiGo3 Simulator Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"✗ Error: Python 3.8+ required (you have {sys.version})")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Get script directory
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    venv_dir = script_dir / "venv"
    
    # Check if venv exists
    if venv_dir.exists():
        print(f"→ Virtual environment already exists at {venv_dir}")
        response = input("  Recreate it? [y/N] ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_dir)
        else:
            print("  Keeping existing environment")
    
    # Create venv if needed
    if not venv_dir.exists():
        print("→ Creating virtual environment...")
        import venv
        venv.create(venv_dir, with_pip=True)
        print(f"✓ Created {venv_dir}")
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
        activate_cmd = str(venv_dir / "Scripts" / "activate.bat")
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
        activate_cmd = f"source {venv_dir / 'bin' / 'activate'}"
    
    # Upgrade pip
    print("→ Upgrading pip...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip", "-q"], check=True)
    
    # Install dependencies
    print("→ Installing dependencies...")
    subprocess.run([str(pip_path), "install", "opencv-python", "numpy", "-q"], check=True)
    print("✓ Installed opencv-python, numpy")
    
    # Install package in editable mode
    subprocess.run([str(pip_path), "install", "-e", ".", "-q"], check=True)
    print("✓ Installed gopigo_sim (editable)")
    
    # Verify installation
    print("→ Verifying installation...")
    result = subprocess.run(
        [str(python_path), "-c", 
         "from gopigo_sim import EasyGoPiGo3; import cv2; import numpy; "
         "print(f'✓ All imports successful (OpenCV {cv2.__version__}, NumPy {numpy.__version__})')"],
        capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"✗ Verification failed: {result.stderr}")
        sys.exit(1)
    
    # Print success message
    print()
    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print()
    print("To use the simulator:")
    print()
    print(f"  1. Activate the environment:")
    print(f"     {activate_cmd}")
    print()
    print(f"  2. Run your code:")
    print(f"     python examples/example_student_code.py")
    print()
    print(f"  3. When done, deactivate:")
    print(f"     deactivate")
    print()


if __name__ == "__main__":
    main()
