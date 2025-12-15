"""
robot.py - Differential-drive robot kinematics.

The robot state is (x, y, theta) where:
- x, y: position in world coordinates (cm)
- theta: heading angle in radians (0 = facing +Y, positive = counterclockwise)

Differential drive model:
- Two wheels separated by WHEEL_BASE
- Each wheel can spin at different speeds
- Robot turns by varying wheel speeds
"""

import math
from dataclasses import dataclass, field
from typing import Tuple, List


@dataclass
class RobotState:
    """Immutable snapshot of robot state for history tracking."""
    x: float
    y: float
    theta: float
    time: float


@dataclass
class Robot:
    """
    Differential-drive robot with GoPiGo3-like parameters.
    
    The kinematics are simplified but physically plausible:
    - Linear velocity v = (v_left + v_right) / 2
    - Angular velocity w = (v_right - v_left) / wheel_base
    """
    # Position and heading
    x: float = 0.0          # cm
    y: float = 0.0          # cm
    theta: float = 0.0      # radians (0 = facing +Y)
    
    # Physical parameters (approximately match GoPiGo3)
    wheel_base: float = 11.5    # Distance between wheels in cm
    wheel_radius: float = 3.25  # Wheel radius in cm
    
    # Motor state
    left_speed: float = 0.0     # Left wheel speed (degrees per second)
    right_speed: float = 0.0    # Right wheel speed (degrees per second)
    default_speed: float = 300  # Default speed in DPS
    
    # Simulation state
    time: float = 0.0           # Simulation time in seconds
    history: List[RobotState] = field(default_factory=list)
    
    def set_motor_speeds(self, left_dps: float, right_dps: float):
        """
        Set wheel speeds in degrees per second (matching GoPiGo3 API).
        
        Positive = forward rotation for that wheel.
        """
        self.left_speed = left_dps
        self.right_speed = right_dps
    
    def _dps_to_cms(self, dps: float) -> float:
        """Convert degrees per second to cm per second."""
        # circumference = 2 * pi * r
        # (dps / 360) rotations per second * circumference = cm/s
        return (dps / 360.0) * (2 * math.pi * self.wheel_radius)
    
    def update(self, dt: float):
        """
        Advance the simulation by dt seconds.
        
        Uses simple Euler integration of differential drive equations:
        - v = (v_l + v_r) / 2
        - omega = (v_r - v_l) / L
        - x' = v * sin(theta)  # Note: our Y is forward, X is right
        - y' = v * cos(theta)
        - theta' = omega
        """
        # Record state before update
        self.history.append(RobotState(self.x, self.y, self.theta, self.time))
        
        # Convert wheel speeds to linear velocities (cm/s)
        v_left = self._dps_to_cms(self.left_speed)
        v_right = self._dps_to_cms(self.right_speed)
        
        # Compute robot velocities
        v = (v_left + v_right) / 2.0  # Linear velocity
        omega = (v_right - v_left) / self.wheel_base  # Angular velocity
        
        # Update pose using Euler integration
        # In our coordinate system: +Y is forward, +X is right
        # theta=0 means facing +Y, positive theta is counterclockwise
        self.x += v * math.sin(self.theta) * dt
        self.y += v * math.cos(self.theta) * dt
        self.theta += omega * dt
        
        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        self.time += dt
    
    def get_pose(self) -> Tuple[float, float, float]:
        """Get current (x, y, theta) pose."""
        return (self.x, self.y, self.theta)
    
    def reset(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0):
        """Reset robot to a specific pose and clear history."""
        self.x = x
        self.y = y
        self.theta = theta
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.time = 0.0
        self.history.clear()
    
    def get_camera_pose(self) -> Tuple[float, float, float]:
        """
        Get the camera position and heading.
        
        The camera is mounted at the front of the robot.
        Returns (cam_x, cam_y, cam_theta).
        """
        # Camera offset from robot center (approximately 5cm forward)
        camera_offset = 5.0
        cam_x = self.x + camera_offset * math.sin(self.theta)
        cam_y = self.y + camera_offset * math.cos(self.theta)
        return (cam_x, cam_y, self.theta)


def create_robot(x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> Robot:
    """Factory function to create a robot at a specific pose."""
    return Robot(x=x, y=y, theta=theta)
