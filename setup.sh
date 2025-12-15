#!/bin/bash
# setup.sh - Set up virtual environment for GoPiGo3 Simulator
#
# Usage:
#   ./setup.sh          # Create venv and install dependencies
#   source venv/bin/activate   # Activate the environment
#   python examples/example_student_code.py  # Run your code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="venv"
PYTHON_CMD=""

echo "========================================"
echo "GoPiGo3 Simulator Setup"
echo "========================================"

# Find Python 3
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON_CMD="$cmd"
            echo "✓ Found Python $version ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "✗ Error: Python 3.8+ required but not found"
    echo "  Install with: sudo apt install python3 python3-venv python3-full"
    exit 1
fi

# Check for venv module
if ! "$PYTHON_CMD" -c "import venv" 2>/dev/null; then
    echo "✗ Error: Python venv module not found"
    echo "  Install with: sudo apt install python3-venv python3-full"
    exit 1
fi

# Create virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "→ Virtual environment already exists at ./$VENV_DIR"
    read -p "  Recreate it? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
        echo "✓ Recreated virtual environment"
    fi
else
    echo "→ Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "✓ Created virtual environment at ./$VENV_DIR"
fi

# Activate and install
echo "→ Installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip first
pip install --upgrade pip --quiet

# Install dependencies
pip install opencv-python numpy --quiet

# Install the package in editable mode
pip install -e . --quiet

echo "✓ Installed: opencv-python, numpy, gopigo_sim"

# Verify installation
echo "→ Verifying installation..."
python -c "from gopigo_sim import EasyGoPiGo3; print('✓ gopigo_sim imports successfully')"
python -c "import cv2; print(f'✓ OpenCV {cv2.__version__}')"
python -c "import numpy; print(f'✓ NumPy {numpy.__version__}')"

echo ""
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "To use the simulator:"
echo ""
echo "  1. Activate the environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run your code:"
echo "     python examples/example_student_code.py"
echo ""
echo "  3. When done, deactivate:"
echo "     deactivate"
echo ""
