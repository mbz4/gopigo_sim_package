"""
GoPiGo3 Educational Simulator
=============================

A Python-only simulator for GoPiGo3 robots with vision-based navigation.

Quick Start:
    # Replace your real robot import:
    # from easygopigo3 import EasyGoPiGo3
    
    # With the simulator:
    from gopigo_sim import EasyGoPiGo3
    
    # Your existing code works unchanged!
    gpg = EasyGoPiGo3()
    gpg.forward()
    frame = gpg.capture_frame()

Available Scenarios:
    gpg = EasyGoPiGo3(scenario='simple_gate')   # Two pillars ahead
    gpg = EasyGoPiGo3(scenario='narrow_gate')   # Tighter gap
    gpg = EasyGoPiGo3(scenario='slalom')        # Multiple gates

Deterministic Testing:
    from gopigo_sim import create_deterministic_simulator
    gpg = create_deterministic_simulator(seed=42)  # Same layout every time

Debugging:
    from gopigo_sim.viz import SimulatorViewer
    viewer = SimulatorViewer(gpg)
    viewer.run()  # Interactive window
"""

# Core API - drop-in replacement for real robot
from .simulator import (
    EasyGoPiGo3,
    create_simulator,
    create_deterministic_simulator,
)

# World building
from .world import (
    World,
    Pillar,
    load_scenario,
)

# For advanced use
from .robot import Robot, create_robot
from .camera import Camera, CameraConfig, create_camera

__version__ = "0.1.0"
__all__ = [
    # Main API
    'EasyGoPiGo3',
    'create_simulator', 
    'create_deterministic_simulator',
    # World
    'World',
    'Pillar',
    'load_scenario',
    # Advanced
    'Robot',
    'Camera',
    'CameraConfig',
]
