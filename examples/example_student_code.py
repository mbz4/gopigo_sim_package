"""
example_student_code.py - Demonstration of vision-based navigation

This example shows how student code can work unchanged with both
the real robot and the simulator. Just change the import!

Task: Drive between two colored pillars (green on left, orange on right)
"""

import cv2
import numpy as np
import time

# ============================================================
# CHANGE THIS IMPORT TO SWITCH BETWEEN REAL AND SIMULATED ROBOT
# ============================================================
# For real robot:
# from easygopigo3 import EasyGoPiGo3

# For simulator:
from gopigo_sim import EasyGoPiGo3
from gopigo_sim.viz import draw_topdown_view
# ============================================================


def find_colored_blob(frame, color_name):
    """
    Find a colored blob in the frame using HSV thresholding.
    
    Args:
        frame: BGR image from camera
        color_name: 'green' or 'orange'
    
    Returns:
        dict with 'center', 'area', 'found' or None if not found
    """
    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define color ranges (tuned for simulator colors)
    color_ranges = {
        'green': {
            'lower': np.array([35, 100, 100]),
            'upper': np.array([85, 255, 255])
        },
        'orange': {
            'lower': np.array([10, 100, 100]),
            'upper': np.array([25, 255, 255])
        }
    }
    
    if color_name not in color_ranges:
        return None
    
    # Create mask
    lower = color_ranges[color_name]['lower']
    upper = color_ranges[color_name]['upper']
    mask = cv2.inRange(hsv, lower, upper)
    
    # Optional: clean up mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Find largest contour
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    
    if area < 100:  # Minimum area threshold
        return None
    
    # Get centroid
    M = cv2.moments(largest)
    if M['m00'] == 0:
        return None
    
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    
    return {
        'center': (cx, cy),
        'area': area,
        'found': True,
        'color': color_name
    }


def create_debug_display(gpg, frame, green_blob, orange_blob, status_text):
    """
    Create a combined debug display with camera view and top-down view.
    """
    # Get simulator internals for top-down view
    sim = gpg._sim
    
    # Draw detection markers on camera frame
    display_frame = frame.copy()
    frame_center_x = frame.shape[1] // 2
    
    # Draw center line
    cv2.line(display_frame, (frame_center_x, 0), (frame_center_x, frame.shape[0]), 
             (255, 255, 255), 1)
    
    # Draw detected blobs
    if green_blob:
        cx, cy = green_blob['center']
        cv2.circle(display_frame, (cx, cy), 15, (0, 255, 0), 2)
        cv2.putText(display_frame, f"G:{green_blob['area']:.0f}", (cx-30, cy-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    if orange_blob:
        cx, cy = orange_blob['center']
        cv2.circle(display_frame, (cx, cy), 15, (0, 165, 255), 2)
        cv2.putText(display_frame, f"O:{orange_blob['area']:.0f}", (cx-30, cy-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
    
    # Draw midpoint if both found
    if green_blob and orange_blob:
        mid_x = (green_blob['center'][0] + orange_blob['center'][0]) // 2
        mid_y = (green_blob['center'][1] + orange_blob['center'][1]) // 2
        cv2.drawMarker(display_frame, (mid_x, mid_y), (0, 255, 255), 
                       cv2.MARKER_CROSS, 20, 2)
    
    # Add status text to camera view
    cv2.putText(display_frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(display_frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Create top-down view (same height as camera frame)
    topdown = draw_topdown_view(sim.world, sim.robot, size=frame.shape[0])
    
    # Add labels
    cv2.putText(display_frame, "Camera View", (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(topdown, "Top-Down View", (10, topdown.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Combine side by side
    combined = np.hstack([display_frame, topdown])
    
    return combined


def navigate_between_pillars(gpg, target_speed=200):
    """
    Navigate between green (left) and orange (right) pillars.
    
    Strategy:
    1. Find both pillars in the camera view
    2. Calculate the midpoint between them
    3. Steer to keep the midpoint centered
    4. Stop when pillars are close (large area)
    
    Returns True if goal reached, False if cancelled.
    """
    gpg.set_speed(target_speed)
    
    # Camera center X coordinate
    frame_center_x = 320  # Half of 640
    
    print("Starting navigation...")
    print("Looking for green (left) and orange (right) pillars")
    print("Press Q or Esc to quit, R to reset")
    
    goal_reached = False
    
    while True:
        # Capture frame
        frame = gpg.capture_frame()
        
        # Find both pillars
        green_blob = find_colored_blob(frame, 'green')
        orange_blob = find_colored_blob(frame, 'orange')
        
        # Navigation logic
        if green_blob and orange_blob:
            # Both pillars visible - navigate to midpoint
            green_x = green_blob['center'][0]
            orange_x = orange_blob['center'][0]
            midpoint_x = (green_x + orange_x) / 2
            
            # Calculate error from center
            error = (midpoint_x - frame_center_x) / frame_center_x  # Normalized [-1, 1]
            
            # Check if we should stop (pillars are close)
            avg_area = (green_blob['area'] + orange_blob['area']) / 2
            
            if avg_area > 15000:  # Pillars are very close
                gpg.stop()
                status = "GOAL REACHED! Press R to reset, Q to quit"
                goal_reached = True
            else:
                # Proportional steering
                turn_strength = int(error * 50)
                left_speed = 50 - turn_strength
                right_speed = 50 + turn_strength
                left_speed = max(-100, min(100, left_speed))
                right_speed = max(-100, min(100, right_speed))
                gpg.steer(left_speed, right_speed)
                status = f"Navigating: err={error:.2f} L={left_speed} R={right_speed}"
            
        elif green_blob or orange_blob:
            # Only one pillar visible - turn toward center
            blob = green_blob or orange_blob
            blob_x = blob['center'][0]
            
            if blob_x < frame_center_x:
                gpg.steer(60, 40)
                status = f"Searching: only {blob['color']} (turning right)"
            else:
                gpg.steer(40, 60)
                status = f"Searching: only {blob['color']} (turning left)"
        else:
            # No pillars visible - search by spinning slowly
            gpg.steer(30, 60)
            status = "Searching for pillars..."
        
        # Create and show debug display
        display = create_debug_display(gpg, frame, green_blob, orange_blob, status)
        cv2.imshow('GoPiGo3 Navigation', display)
        
        # Handle keyboard input
        key = cv2.waitKey(50) & 0xFF
        
        if key == ord('q') or key == 27:  # Q or Esc
            print("\nQuit by user")
            gpg.stop()
            return False
        elif key == ord('r'):  # R to reset
            print("\nResetting position...")
            gpg.stop()
            gpg.reset()
            goal_reached = False
        
        # Small delay for readability
        if not goal_reached:
            time.sleep(0.05)


def main():
    """Main entry point."""
    print("=" * 50)
    print("GoPiGo3 Vision Navigation Demo")
    print("=" * 50)
    print()
    print("Controls:")
    print("  Q / Esc  - Quit")
    print("  R        - Reset robot position")
    print()
    
    # Initialize robot (works with both real and simulated!)
    gpg = EasyGoPiGo3(scenario='simple_gate')
    
    try:
        # Run navigation
        navigate_between_pillars(gpg)
        
        # Keep window open until user closes it
        print("\nNavigation complete. Press any key in the window to close.")
        cv2.waitKey(0)
        
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C")
    finally:
        gpg.stop()
        gpg.close()
        cv2.destroyAllWindows()
        
        # Show final position (simulator only)
        if hasattr(gpg, 'get_pose'):
            x, y, theta = gpg.get_pose()
            print(f"Final position: ({x:.1f}, {y:.1f}), heading: {np.degrees(theta):.1f}°")


if __name__ == '__main__':
    main()
