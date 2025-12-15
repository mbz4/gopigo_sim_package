"""
camera.py - Synthetic camera image generation.

Generates OpenCV-compatible BGR images showing what the robot would see.
Uses a simple pinhole camera model to project 3D pillars onto 2D image.

The camera model:
- Resolution: 640x360 (configurable)
- Horizontal FOV: ~60 degrees (configurable)
- Pillars are rendered as vertical rectangles
- Size scales inversely with distance (perspective)
"""

import math
import numpy as np
import cv2
from dataclasses import dataclass
from typing import List, Tuple, Optional

from .world import World, Pillar
from .robot import Robot


@dataclass
class CameraConfig:
    """Camera intrinsic parameters."""
    width: int = 640          # Image width in pixels
    height: int = 360         # Image height in pixels
    fov_horizontal: float = 60.0  # Horizontal field of view in degrees
    
    # Rendering parameters
    sky_color: Tuple[int, int, int] = (200, 180, 160)    # BGR
    ground_color: Tuple[int, int, int] = (60, 80, 60)    # BGR
    horizon_y: float = 0.45   # Horizon position (0=top, 1=bottom)
    
    # Distance limits for rendering
    min_distance: float = 5.0    # Don't render closer than this (cm)
    max_distance: float = 500.0  # Don't render farther than this (cm)
    
    @property
    def focal_length(self) -> float:
        """Compute focal length in pixels from FOV."""
        # f = (width/2) / tan(fov/2)
        fov_rad = math.radians(self.fov_horizontal)
        return (self.width / 2) / math.tan(fov_rad / 2)
    
    @property
    def center_x(self) -> float:
        """Image center X coordinate."""
        return self.width / 2
    
    @property
    def center_y(self) -> float:
        """Image center Y coordinate."""
        return self.height / 2


class Camera:
    """
    Synthetic camera that renders the world from the robot's perspective.
    
    Usage:
        camera = Camera(world, robot)
        frame = camera.capture()  # Returns BGR numpy array
    """
    
    def __init__(self, world: World, robot: Robot, config: CameraConfig = None):
        self.world = world
        self.robot = robot
        self.config = config or CameraConfig()
        
        # Pre-allocate frame buffer
        self._frame = np.zeros(
            (self.config.height, self.config.width, 3), 
            dtype=np.uint8
        )
    
    def capture(self) -> np.ndarray:
        """
        Capture a frame from the robot's perspective.
        
        Returns:
            BGR image as numpy array (height, width, 3)
        """
        # Clear frame with background
        self._draw_background()
        
        # Get camera pose
        cam_x, cam_y, cam_theta = self.robot.get_camera_pose()
        
        # Collect visible pillars with their projected info
        visible_pillars = []
        
        for pillar in self.world.pillars:
            proj = self._project_pillar(pillar, cam_x, cam_y, cam_theta)
            if proj is not None:
                visible_pillars.append((proj['distance'], pillar, proj))
        
        # Sort by distance (far to near) for painter's algorithm
        visible_pillars.sort(key=lambda x: -x[0])
        
        # Render pillars
        for _, pillar, proj in visible_pillars:
            self._draw_pillar(pillar, proj)
        
        return self._frame.copy()
    
    def _draw_background(self):
        """Draw sky and ground."""
        cfg = self.config
        horizon_pixel = int(cfg.height * cfg.horizon_y)
        
        # Sky (upper portion)
        self._frame[:horizon_pixel, :] = cfg.sky_color
        
        # Ground (lower portion) - simple gradient for depth cue
        ground = self._frame[horizon_pixel:, :]
        for i in range(ground.shape[0]):
            # Darken ground toward horizon
            t = i / ground.shape[0]
            color = tuple(int(c * (0.7 + 0.3 * t)) for c in cfg.ground_color)
            ground[i, :] = color
    
    def _project_pillar(self, pillar: Pillar, cam_x: float, cam_y: float, 
                        cam_theta: float) -> Optional[dict]:
        """
        Project a pillar to screen coordinates.
        
        Returns dict with screen coordinates and size, or None if not visible.
        """
        cfg = self.config
        
        # Transform pillar to camera-local coordinates
        # (cam_theta=0 means camera faces +Y in world coords)
        dx = pillar.x - cam_x
        dy = pillar.y - cam_y
        
        # Rotate to camera frame (camera looks along +Y in local frame)
        cos_t = math.cos(-cam_theta)
        sin_t = math.sin(-cam_theta)
        local_x = dx * cos_t - dy * sin_t   # Right is positive
        local_y = dx * sin_t + dy * cos_t   # Forward is positive
        
        # Check if pillar is in front of camera
        if local_y < cfg.min_distance:
            return None
        if local_y > cfg.max_distance:
            return None
        
        # Check if pillar is within horizontal FOV (with some margin)
        angle_to_pillar = math.atan2(local_x, local_y)
        fov_rad = math.radians(cfg.fov_horizontal / 2)
        if abs(angle_to_pillar) > fov_rad * 1.2:  # 20% margin
            return None
        
        # Project to screen coordinates
        # screen_x = f * (local_x / local_y) + center_x
        screen_x = cfg.focal_length * (local_x / local_y) + cfg.center_x
        
        # Calculate apparent size based on distance
        distance = math.sqrt(local_x**2 + local_y**2)
        
        # Pillar width on screen (using diameter)
        apparent_width = cfg.focal_length * (pillar.radius * 2) / local_y
        
        # Pillar height on screen
        # The pillar sits on the ground, so its base is at ground level
        # and top is at pillar.height above ground
        apparent_height = cfg.focal_length * pillar.height / local_y
        
        # Vertical position: base of pillar should be at ground level
        # Ground level at this distance projects to a certain y-pixel
        horizon_y = cfg.height * cfg.horizon_y
        # Base of pillar (on ground) projects below horizon
        # The further away, the closer to horizon
        base_y = horizon_y + cfg.focal_length * 0.1 / local_y  # Approximate
        
        return {
            'screen_x': screen_x,
            'screen_y_top': base_y - apparent_height,
            'screen_y_bottom': base_y,
            'width': apparent_width,
            'height': apparent_height,
            'distance': distance,
        }
    
    def _draw_pillar(self, pillar: Pillar, proj: dict):
        """Draw a pillar on the frame."""
        # Calculate rectangle bounds
        x_center = proj['screen_x']
        width = max(2, int(proj['width']))  # At least 2 pixels wide
        height = max(4, int(proj['height']))
        
        x1 = int(x_center - width / 2)
        x2 = int(x_center + width / 2)
        y1 = int(proj['screen_y_top'])
        y2 = int(proj['screen_y_bottom'])
        
        # Clamp to frame bounds
        x1 = max(0, min(x1, self.config.width - 1))
        x2 = max(0, min(x2, self.config.width))
        y1 = max(0, min(y1, self.config.height - 1))
        y2 = max(0, min(y2, self.config.height))
        
        if x1 >= x2 or y1 >= y2:
            return
        
        # Get base color and apply distance-based shading
        base_color = pillar.bgr
        # Darken with distance for depth perception
        shade = max(0.4, 1.0 - (proj['distance'] / 400.0))
        color = tuple(int(c * shade) for c in base_color)
        
        # Draw main body
        cv2.rectangle(self._frame, (x1, y1), (x2, y2), color, -1)
        
        # Add simple edge highlight for 3D effect
        if width > 4:
            # Lighter left edge
            highlight = tuple(min(255, int(c * 1.3)) for c in color)
            cv2.line(self._frame, (x1, y1), (x1, y2), highlight, 1)
            # Darker right edge  
            shadow = tuple(int(c * 0.7) for c in color)
            cv2.line(self._frame, (x2-1, y1), (x2-1, y2), shadow, 1)


def create_camera(world: World, robot: Robot, 
                  width: int = 640, height: int = 360) -> Camera:
    """Factory function to create a camera with custom resolution."""
    config = CameraConfig(width=width, height=height)
    return Camera(world, robot, config)
