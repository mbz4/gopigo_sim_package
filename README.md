# GoPiGo3 Educational Simulator

A Python-only simulator for GoPiGo3 robots focused on vision-based navigation tasks. No ROS, no Gazebo—just Python, OpenCV, and NumPy.

## Features

- **Drop-in API replacement**: Same interface as `easygopigo3.EasyGoPiGo3`
- **Synthetic camera**: Generates OpenCV-compatible BGR frames
- **HSV-ready colors**: Pillars render with colors that work with standard blob detection
- **Deterministic replay**: Use seeds for reproducible testing and grading
- **Debug visualization**: Top-down view with robot path and FOV cone

## Installation

### Quick Setup (Recommended)

**Linux/macOS:**
```bash
cd gopigo_sim_package
./setup.sh
source venv/bin/activate
```

**Windows:**
```cmd
cd gopigo_sim_package
setup.bat
venv\Scripts\activate.bat
```

**Cross-platform (Python):**
```bash
cd gopigo_sim_package
python3 setup_venv.py
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate.bat   # Windows
```

**Using Make:**
```bash
make setup
source venv/bin/activate
```

### Manual Setup

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install opencv-python numpy

# Install the simulator package
pip install -e .
```

### Prerequisites

- Python 3.8+
- On Ubuntu/Debian, you may need: `sudo apt install python3-venv python3-full`

### After Setup

Once set up, you can quickly activate the environment:
```bash
source activate.sh
```

## Running the Demos

**Vision Navigation Demo** (autonomous driving between pillars):
```bash
source activate.sh
python examples/example_student_code.py
```

**Interactive Demo** (manual driving with arrow keys):
```bash
source activate.sh
python examples/interactive_demo.py
```

### Controls

| Key | Action |
|-----|--------|
| Arrow keys | Drive robot |
| Space | Stop |
| R | Reset position |
| Q / Esc | Quit |
| 1-4 | Switch scenarios (interactive demo) |

## Quick Start

```python
# Just change your import!
# from easygopigo3 import EasyGoPiGo3  # Real robot
from gopigo_sim import EasyGoPiGo3      # Simulator

# Your existing code works unchanged
gpg = EasyGoPiGo3()
gpg.forward()
frame = gpg.capture_frame()  # Returns BGR numpy array
gpg.stop()
```

## Scenarios

```python
# Built-in scenarios
gpg = EasyGoPiGo3(scenario='simple_gate')   # Two pillars forming a gate
gpg = EasyGoPiGo3(scenario='narrow_gate')   # Tighter gap
gpg = EasyGoPiGo3(scenario='slalom')        # Multiple gates to navigate

# Deterministic random worlds (same seed = same layout)
from gopigo_sim import create_deterministic_simulator
gpg = create_deterministic_simulator(seed=42)

# Custom worlds
from gopigo_sim import World, Pillar
world = World(pillars=[
    Pillar(x=-30, y=100, color='green'),
    Pillar(x=30, y=100, color='orange'),
])
gpg = EasyGoPiGo3(world=world)
```

## API Reference

### Motion Commands

| Method | Description |
|--------|-------------|
| `forward()` | Drive forward at current speed |
| `backward()` | Drive backward |
| `left()` | Spin left in place |
| `right()` | Spin right in place |
| `stop()` | Stop all motors |
| `set_speed(dps)` | Set default speed (degrees/sec) |
| `steer(left%, right%)` | Differential steering (-100 to 100) |

### Camera

```python
frame = gpg.capture_frame()  # Returns 640x360 BGR numpy array
```

### Simulator-Only Methods

```python
x, y, theta = gpg.get_pose()    # Get robot position
gpg.reset(x=0, y=0, theta=0)    # Reset position
gpg.step(dt=0.02)               # Manual time step (for testing)
```

## HSV Color Ranges

These ranges work well with the simulator's pillar colors:

```python
# Green pillars
green_lower = np.array([35, 100, 100])
green_upper = np.array([85, 255, 255])

# Orange pillars
orange_lower = np.array([10, 100, 100])
orange_upper = np.array([25, 255, 255])
```

## Debug Visualization

```python
from gopigo_sim.viz import SimulatorViewer

gpg = EasyGoPiGo3(scenario='slalom')
viewer = SimulatorViewer(gpg)
viewer.run()  # Opens interactive window
# Arrow keys: manual control
# Space: stop
# R: reset
# Q: quit
```

## Module Architecture

```
gopigo_sim/
├── __init__.py      # Package exports
├── world.py         # World state, pillars, scenarios
├── robot.py         # Differential-drive kinematics
├── camera.py        # Synthetic camera rendering
├── simulator.py     # EasyGoPiGo3-compatible interface
└── viz.py           # Debug visualization tools
```

## Example: Navigate Between Pillars

```python
import cv2
import numpy as np
from gopigo_sim import EasyGoPiGo3

def find_blob(frame, color_name):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    ranges = {
        'green': ([35, 100, 100], [85, 255, 255]),
        'orange': ([10, 100, 100], [25, 255, 255]),
    }
    
    lower, upper = ranges[color_name]
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                    cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)
    if M['m00'] == 0:
        return None
    
    return (int(M['m10']/M['m00']), int(M['m01']/M['m00']))

# Main navigation loop
gpg = EasyGoPiGo3(scenario='simple_gate')
gpg.set_speed(200)

while True:
    frame = gpg.capture_frame()
    green = find_blob(frame, 'green')
    orange = find_blob(frame, 'orange')
    
    if green and orange:
        midpoint = (green[0] + orange[0]) / 2
        error = (midpoint - 320) / 320  # Normalized error
        
        gpg.steer(50 - int(error*30), 50 + int(error*30))
    else:
        gpg.steer(30, 60)  # Search
```

## Pedagogical Design

This simulator prioritizes:

1. **Simplicity**: Each module is <200 lines, well-commented
2. **Debuggability**: Visual feedback, inspectable state
3. **Reproducibility**: Deterministic seeds for grading
4. **Real-world transfer**: Same API as actual robot

Not priorities:
- Physics accuracy (simplified differential drive)
- 3D realism (basic perspective projection)
- Performance optimization

## License

MIT - Free for educational use.
