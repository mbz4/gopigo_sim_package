"""
simulator.py - EasyGoPiGo3-compatible simulator interface.

This module provides a drop-in replacement for easygopigo3.EasyGoPiGo3
that runs in simulation. Student code can switch between real and
simulated robots by changing a single import:

    # For real robot:
    # from easygopigo3 import EasyGoPiGo3
    
    # For simulation:
    from gopigo_sim import EasyGoPiGo3
    
    gpg = EasyGoPiGo3()
    gpg.forward()
    ...
"""

import time
import threading
import numpy as np
from typing import Optional, Callable

from .world import World, load_scenario
from .robot import Robot, create_robot
from .camera import Camera, create_camera, CameraConfig


class SimulatedGoPiGo3:
    """
    Core simulator class.
    
    Runs the physics simulation in a background thread to mimic
    the real robot's asynchronous behavior.
    """
    
    def __init__(self, world: World = None, dt: float = 0.02):
        """
        Initialize the simulator.
        
        Args:
            world: World configuration. Defaults to a simple gate scenario.
            dt: Simulation timestep in seconds (default 50Hz)
        """
        self.world = world or load_scenario('simple_gate')
        self.robot = create_robot()
        self.camera = create_camera(self.world, self.robot)
        
        self.dt = dt
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        
        # Start simulation loop
        self._start_simulation()
    
    def _start_simulation(self):
        """Start the background simulation thread."""
        self._running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
    
    def _simulation_loop(self):
        """Background thread that updates physics."""
        while self._running:
            with self._lock:
                self.robot.update(self.dt)
            time.sleep(self.dt)
    
    def stop_simulation(self):
        """Stop the simulation thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def step(self, dt: float = None):
        """
        Manually step the simulation (for deterministic testing).
        
        Use this instead of the background thread when you need
        exact reproducibility.
        """
        with self._lock:
            self.robot.update(dt or self.dt)
    
    def capture_frame(self) -> np.ndarray:
        """Capture a camera frame."""
        with self._lock:
            return self.camera.capture()
    
    def get_pose(self):
        """Get robot (x, y, theta) pose."""
        with self._lock:
            return self.robot.get_pose()
    
    def reset(self, x: float = 0, y: float = 0, theta: float = 0):
        """Reset robot to specified pose."""
        with self._lock:
            self.robot.reset(x, y, theta)


class EasyGoPiGo3:
    """
    Drop-in replacement for easygopigo3.EasyGoPiGo3.
    
    Implements the core motion API:
    - forward(), backward()
    - left(), right()
    - steer(left_speed, right_speed)
    - stop()
    - set_speed(speed)
    
    Also provides simulated camera access.
    """
    
    # Default speed in degrees per second (matches real GoPiGo3)
    DEFAULT_SPEED = 300
    
    def __init__(self, world: World = None, scenario: str = None):
        """
        Initialize the simulated GoPiGo3.
        
        Args:
            world: Custom World object
            scenario: Name of built-in scenario ('simple_gate', 'slalom', etc.)
        """
        if scenario:
            world = load_scenario(scenario)
        
        self._sim = SimulatedGoPiGo3(world=world)
        self._speed = self.DEFAULT_SPEED
        
        # Simulated sensors/peripherals
        self._camera = _SimulatedCamera(self._sim)
    
    # ============ Motion API (matches real EasyGoPiGo3) ============
    
    def set_speed(self, speed: int):
        """
        Set the default speed for motion commands.
        
        Args:
            speed: Speed in degrees per second (typical range: 100-500)
        """
        self._speed = speed
    
    def get_speed(self) -> int:
        """Get the current speed setting."""
        return self._speed
    
    def forward(self):
        """Drive forward at the current speed (non-blocking)."""
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(self._speed, self._speed)
    
    def backward(self):
        """Drive backward at the current speed (non-blocking)."""
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(-self._speed, -self._speed)
    
    def left(self):
        """Spin left in place (non-blocking)."""
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(-self._speed, self._speed)
    
    def right(self):
        """Spin right in place (non-blocking)."""
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(self._speed, -self._speed)
    
    def stop(self):
        """Stop all motors."""
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(0, 0)
    
    def steer(self, left_percent: int, right_percent: int):
        """
        Set individual motor speeds as percentages of max speed.
        
        This is the key method for differential steering.
        
        Args:
            left_percent: Left motor speed (-100 to 100)
            right_percent: Right motor speed (-100 to 100)
        """
        left_speed = self._speed * (left_percent / 100.0)
        right_speed = self._speed * (right_percent / 100.0)
        
        with self._sim._lock:
            self._sim.robot.set_motor_speeds(left_speed, right_speed)
    
    def set_motor_dps(self, port, dps: int):
        """
        Set motor speed directly in degrees per second.
        
        Args:
            port: Motor port (MOTOR_LEFT or MOTOR_RIGHT constant, or string)
            dps: Speed in degrees per second
        """
        # Simplified: we accept 'left'/'right' or port constants
        port_str = str(port).lower()
        with self._sim._lock:
            if 'left' in port_str or port == 1:
                self._sim.robot.left_speed = dps
            elif 'right' in port_str or port == 2:
                self._sim.robot.right_speed = dps
    
    # ============ Simulated Sensors ============
    
    def init_camera(self, resolution: str = "640x360") -> '_SimulatedCamera':
        """
        Initialize the Pi Camera (simulated).
        
        Args:
            resolution: Camera resolution string (e.g., "640x360")
        
        Returns:
            Simulated camera object
        """
        # Parse resolution
        if 'x' in resolution:
            w, h = map(int, resolution.lower().split('x'))
            self._camera._config = CameraConfig(width=w, height=h)
            self._sim.camera = Camera(
                self._sim.world, 
                self._sim.robot,
                self._camera._config
            )
        return self._camera
    
    # ============ Simulation-Specific API ============
    
    def get_pose(self):
        """
        [Simulator only] Get robot pose as (x, y, theta).
        
        Not available on real robot - use for debugging only.
        """
        return self._sim.get_pose()
    
    def reset(self, x: float = 0, y: float = 0, theta: float = 0):
        """
        [Simulator only] Reset robot position.
        """
        self._sim.reset(x, y, theta)
    
    def capture_frame(self) -> np.ndarray:
        """
        Capture a camera frame directly.
        
        Convenience method - you can also use init_camera().capture()
        """
        return self._sim.capture_frame()
    
    def step(self, dt: float = 0.02):
        """
        [Simulator only] Manually advance simulation.
        
        Use for deterministic testing without background thread timing.
        """
        self._sim.step(dt)
    
    def close(self):
        """Clean up simulator resources."""
        self._sim.stop_simulation()


class _SimulatedCamera:
    """
    Simulated Pi Camera that matches the interface students expect.
    
    Usage:
        camera = gpg.init_camera()
        frame = camera.capture()  # Returns BGR numpy array
    """
    
    def __init__(self, sim: SimulatedGoPiGo3):
        self._sim = sim
        self._config = CameraConfig()
    
    def capture(self) -> np.ndarray:
        """
        Capture a frame from the simulated camera.
        
        Returns:
            BGR image as numpy array, compatible with OpenCV
        """
        return self._sim.capture_frame()
    
    def start(self):
        """Start camera (no-op in simulator, included for API compatibility)."""
        pass
    
    def stop(self):
        """Stop camera (no-op in simulator, included for API compatibility)."""
        pass


# ============ Convenience Functions ============

def create_simulator(scenario: str = 'simple_gate') -> EasyGoPiGo3:
    """
    Create a simulator with a pre-built scenario.
    
    Available scenarios:
    - 'simple_gate': Two pillars forming a gate 80cm ahead
    - 'narrow_gate': Narrower gate for precision testing
    - 'slalom': Multiple gates in a zigzag pattern
    
    Args:
        scenario: Name of scenario to load
    
    Returns:
        Configured EasyGoPiGo3 simulator instance
    """
    return EasyGoPiGo3(scenario=scenario)


def create_deterministic_simulator(seed: int, num_pillars: int = 4) -> EasyGoPiGo3:
    """
    Create a simulator with deterministic random pillars.
    
    Use the same seed to replay the exact same scenario.
    Great for reproducible testing and grading.
    
    Args:
        seed: Random seed for world generation
        num_pillars: Number of pillars to place
    
    Returns:
        Configured EasyGoPiGo3 simulator instance
    """
    world = World.from_seed(seed, num_pillars)
    return EasyGoPiGo3(world=world)
