"""
viz.py - Visualization tools for debugging.

Provides a top-down view of the world and robot, plus utilities
for displaying camera frames with debug overlays.
"""

import math
import cv2
import numpy as np
from typing import Tuple, Optional

from .world import World, Pillar
from .robot import Robot
from .simulator import EasyGoPiGo3


def draw_topdown_view(world: World, robot: Robot, 
                      size: int = 500, 
                      margin: int = 50) -> np.ndarray:
    """
    Create a top-down visualization of the world and robot.
    
    Args:
        world: World with pillars
        robot: Robot with current pose
        size: Image size in pixels
        margin: Margin around the world
    
    Returns:
        BGR image showing world from above
    """
    img = np.ones((size, size, 3), dtype=np.uint8) * 240  # Light gray background
    
    # Calculate scale to fit world in image
    scale = (size - 2 * margin) / max(world.width, world.height)
    
    def world_to_pixel(wx: float, wy: float) -> Tuple[int, int]:
        """Convert world coordinates to pixel coordinates."""
        px = int(margin + (wx + world.width / 2) * scale)
        py = int(size - margin - wy * scale)  # Y is flipped
        return (px, py)
    
    # Draw world boundary
    x1, y1 = world_to_pixel(-world.width/2, 0)
    x2, y2 = world_to_pixel(world.width/2, world.height)
    cv2.rectangle(img, (x1, y2), (x2, y1), (200, 200, 200), 2)
    
    # Draw grid
    grid_spacing = 50  # cm
    for x in range(-int(world.width/2), int(world.width/2) + 1, grid_spacing):
        p1 = world_to_pixel(x, 0)
        p2 = world_to_pixel(x, world.height)
        cv2.line(img, p1, p2, (220, 220, 220), 1)
    for y in range(0, int(world.height) + 1, grid_spacing):
        p1 = world_to_pixel(-world.width/2, y)
        p2 = world_to_pixel(world.width/2, y)
        cv2.line(img, p1, p2, (220, 220, 220), 1)
    
    # Draw pillars
    for pillar in world.pillars:
        center = world_to_pixel(pillar.x, pillar.y)
        radius = max(3, int(pillar.radius * scale))
        cv2.circle(img, center, radius, pillar.bgr, -1)
        cv2.circle(img, center, radius, (0, 0, 0), 1)  # Black outline
    
    # Draw robot
    rx, ry = world_to_pixel(robot.x, robot.y)
    robot_radius = max(5, int(10 * scale))  # Robot is ~10cm radius
    
    # Robot body (blue circle)
    cv2.circle(img, (rx, ry), robot_radius, (200, 100, 50), -1)
    cv2.circle(img, (rx, ry), robot_radius, (0, 0, 0), 1)
    
    # Robot heading arrow
    arrow_len = robot_radius * 1.5
    ax = int(rx + arrow_len * math.sin(robot.theta))
    ay = int(ry - arrow_len * math.cos(robot.theta))  # Y is flipped
    cv2.arrowedLine(img, (rx, ry), (ax, ay), (0, 0, 200), 2, tipLength=0.3)
    
    # Draw robot path history
    if len(robot.history) > 1:
        points = [(world_to_pixel(s.x, s.y)) for s in robot.history[-200:]]
        for i in range(1, len(points)):
            cv2.line(img, points[i-1], points[i], (180, 180, 255), 1)
    
    # Draw FOV cone
    fov_rad = math.radians(30)  # Half of 60-degree FOV
    fov_length = 100 * scale
    left_angle = robot.theta + fov_rad
    right_angle = robot.theta - fov_rad
    
    lx = int(rx + fov_length * math.sin(left_angle))
    ly = int(ry - fov_length * math.cos(left_angle))
    rrx = int(rx + fov_length * math.sin(right_angle))
    rry = int(ry - fov_length * math.cos(right_angle))
    
    cv2.line(img, (rx, ry), (lx, ly), (100, 200, 100), 1)
    cv2.line(img, (rx, ry), (rrx, rry), (100, 200, 100), 1)
    
    # Add coordinate info
    cv2.putText(img, f"Robot: ({robot.x:.1f}, {robot.y:.1f}) {math.degrees(robot.theta):.1f}°", 
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, f"Time: {robot.time:.2f}s", 
                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    return img


def draw_blob_overlay(frame: np.ndarray, 
                      blobs: list,
                      target_color: str = None) -> np.ndarray:
    """
    Draw blob detection results on a camera frame.
    
    Args:
        frame: Camera frame (BGR)
        blobs: List of detected blobs, each as dict with 'center', 'area', 'color'
        target_color: Optional color to highlight
    
    Returns:
        Frame with blob overlays
    """
    output = frame.copy()
    
    for blob in blobs:
        cx, cy = blob.get('center', (0, 0))
        area = blob.get('area', 0)
        color = blob.get('color', 'unknown')
        
        # Draw crosshairs at blob center
        draw_color = (0, 255, 255)  # Yellow default
        if color == target_color:
            draw_color = (0, 255, 0)  # Green for target
        
        cv2.drawMarker(output, (int(cx), int(cy)), draw_color, 
                       cv2.MARKER_CROSS, 20, 2)
        
        # Draw bounding info
        text = f"{color}: {area:.0f}px"
        cv2.putText(output, text, (int(cx) - 40, int(cy) - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, draw_color, 1)
    
    return output


def create_debug_display(gpg: EasyGoPiGo3, 
                         frame: np.ndarray = None) -> np.ndarray:
    """
    Create a combined debug display with camera and top-down view.
    
    Args:
        gpg: EasyGoPiGo3 simulator instance
        frame: Optional camera frame (will capture if not provided)
    
    Returns:
        Combined debug image
    """
    # Get components from simulator
    sim = gpg._sim
    
    # Capture frame if not provided
    if frame is None:
        frame = sim.capture_frame()
    
    # Create top-down view
    topdown = draw_topdown_view(sim.world, sim.robot, size=360)
    
    # Resize frame to match height
    frame_h = topdown.shape[0]
    frame_resized = cv2.resize(frame, (int(frame.shape[1] * frame_h / frame.shape[0]), frame_h))
    
    # Combine horizontally
    combined = np.hstack([frame_resized, topdown])
    
    return combined


class SimulatorViewer:
    """
    Interactive viewer for the simulator using OpenCV windows.
    
    Usage:
        viewer = SimulatorViewer(gpg)
        viewer.run()  # Opens window, press 'q' to quit
    """
    
    def __init__(self, gpg: EasyGoPiGo3, window_name: str = "GoPiGo Simulator"):
        self.gpg = gpg
        self.window_name = window_name
        self._running = False
    
    def run(self, update_fn: Optional[callable] = None):
        """
        Run the interactive viewer.
        
        Args:
            update_fn: Optional function called each frame with (gpg, frame) args
                      Can be used to run control logic
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self._running = True
        
        print("Simulator Viewer")
        print("  Arrow keys: manual control")
        print("  Space: stop")
        print("  R: reset position")
        print("  Q: quit")
        
        while self._running:
            # Get debug display
            display = create_debug_display(self.gpg)
            cv2.imshow(self.window_name, display)
            
            # Call user update function
            if update_fn:
                frame = self.gpg.capture_frame()
                update_fn(self.gpg, frame)
            
            # Handle keyboard
            key = cv2.waitKey(30) & 0xFF
            
            if key == ord('q'):
                self._running = False
            elif key == ord('r'):
                self.gpg.reset()
            elif key == ord(' '):
                self.gpg.stop()
            elif key == 82:  # Up arrow
                self.gpg.forward()
            elif key == 84:  # Down arrow
                self.gpg.backward()
            elif key == 81:  # Left arrow
                self.gpg.left()
            elif key == 83:  # Right arrow
                self.gpg.right()
        
        cv2.destroyWindow(self.window_name)
        self.gpg.close()
    
    def stop(self):
        """Stop the viewer."""
        self._running = False
