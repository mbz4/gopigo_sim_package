"""
test_camera_output.py - Test that the synthetic camera generates valid images

This script creates sample camera frames and saves them so you can verify
the rendering looks correct for HSV blob detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from gopigo_sim import EasyGoPiGo3, World, Pillar


def test_basic_rendering():
    """Test basic camera rendering with default scenario."""
    print("Testing basic rendering...")
    
    # Create simulator with simple gate
    gpg = EasyGoPiGo3(scenario='simple_gate')
    
    # Capture initial frame
    frame = gpg.capture_frame()
    
    print(f"  Frame shape: {frame.shape}")
    print(f"  Frame dtype: {frame.dtype}")
    print(f"  Frame range: [{frame.min()}, {frame.max()}]")
    
    # Save frame
    cv2.imwrite('/tmp/camera_test_initial.png', frame)
    print("  Saved: /tmp/camera_test_initial.png")
    
    # Move forward a bit and capture again
    gpg.forward()
    for _ in range(50):
        gpg.step(0.02)
    gpg.stop()
    
    frame_after = gpg.capture_frame()
    cv2.imwrite('/tmp/camera_test_after_forward.png', frame_after)
    print("  Saved: /tmp/camera_test_after_forward.png")
    
    gpg.close()
    return True


def test_hsv_detection():
    """Verify that HSV detection works on synthetic frames."""
    print("\nTesting HSV detection...")
    
    gpg = EasyGoPiGo3(scenario='simple_gate')
    frame = gpg.capture_frame()
    
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Green detection
    green_lower = np.array([35, 100, 100])
    green_upper = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    
    # Orange detection
    orange_lower = np.array([10, 100, 100])
    orange_upper = np.array([25, 255, 255])
    orange_mask = cv2.inRange(hsv, orange_lower, orange_upper)
    
    # Count detected pixels
    green_pixels = np.sum(green_mask > 0)
    orange_pixels = np.sum(orange_mask > 0)
    
    print(f"  Green pixels detected: {green_pixels}")
    print(f"  Orange pixels detected: {orange_pixels}")
    
    # Save masks for inspection
    cv2.imwrite('/tmp/green_mask.png', green_mask)
    cv2.imwrite('/tmp/orange_mask.png', orange_mask)
    print("  Saved: /tmp/green_mask.png, /tmp/orange_mask.png")
    
    # Create combined visualization
    vis = frame.copy()
    vis[green_mask > 0] = [0, 255, 0]
    vis[orange_mask > 0] = [0, 165, 255]
    cv2.imwrite('/tmp/detection_overlay.png', vis)
    print("  Saved: /tmp/detection_overlay.png")
    
    gpg.close()
    
    # Check that both colors were detected
    success = green_pixels > 100 and orange_pixels > 100
    print(f"  Detection test: {'PASS' if success else 'FAIL'}")
    return success


def test_different_poses():
    """Test camera from different robot positions."""
    print("\nTesting different poses...")
    
    gpg = EasyGoPiGo3(scenario='simple_gate')
    
    poses = [
        (0, 0, 0, "center_facing_forward"),
        (-20, 0, 0.3, "left_turned_right"),
        (20, 0, -0.3, "right_turned_left"),
        (0, 40, 0, "closer_to_gate"),
    ]
    
    for x, y, theta, name in poses:
        gpg.reset(x, y, theta)
        frame = gpg.capture_frame()
        filename = f'/tmp/pose_{name}.png'
        cv2.imwrite(filename, frame)
        print(f"  Saved: {filename}")
    
    gpg.close()
    return True


def test_deterministic_replay():
    """Test that the same seed produces identical results."""
    print("\nTesting deterministic replay...")
    
    from gopigo_sim import create_deterministic_simulator
    
    # Run simulation twice with same seed
    results = []
    
    for run in range(2):
        gpg = create_deterministic_simulator(seed=12345)
        
        # Run same sequence of actions
        gpg.forward()
        for _ in range(30):
            gpg.step(0.02)
        gpg.steer(60, 40)
        for _ in range(20):
            gpg.step(0.02)
        gpg.stop()
        
        pose = gpg.get_pose()
        results.append(pose)
        gpg.close()
    
    # Compare results
    x1, y1, t1 = results[0]
    x2, y2, t2 = results[1]
    
    match = (abs(x1-x2) < 0.001 and abs(y1-y2) < 0.001 and abs(t1-t2) < 0.001)
    print(f"  Run 1: x={x1:.4f}, y={y1:.4f}, theta={t1:.4f}")
    print(f"  Run 2: x={x2:.4f}, y={y2:.4f}, theta={t2:.4f}")
    print(f"  Determinism test: {'PASS' if match else 'FAIL'}")
    return match


def test_topdown_visualization():
    """Test the debug visualization."""
    print("\nTesting top-down visualization...")
    
    from gopigo_sim.viz import draw_topdown_view, create_debug_display
    
    gpg = EasyGoPiGo3(scenario='slalom')
    
    # Move around to create a path
    gpg.forward()
    for _ in range(50):
        gpg.step(0.02)
    gpg.steer(70, 30)
    for _ in range(30):
        gpg.step(0.02)
    gpg.forward()
    for _ in range(40):
        gpg.step(0.02)
    
    # Create visualizations
    topdown = draw_topdown_view(gpg._sim.world, gpg._sim.robot)
    cv2.imwrite('/tmp/topdown_view.png', topdown)
    print("  Saved: /tmp/topdown_view.png")
    
    debug = create_debug_display(gpg)
    cv2.imwrite('/tmp/debug_combined.png', debug)
    print("  Saved: /tmp/debug_combined.png")
    
    gpg.close()
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("GoPiGo Simulator Camera Tests")
    print("=" * 50)
    
    tests = [
        test_basic_rendering,
        test_hsv_detection,
        test_different_poses,
        test_deterministic_replay,
        test_topdown_visualization,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 50)
    
    print("\nGenerated test images in /tmp/:")
    print("  - camera_test_initial.png      (initial view)")
    print("  - camera_test_after_forward.png (after moving)")
    print("  - green_mask.png, orange_mask.png (HSV masks)")
    print("  - detection_overlay.png        (detected colors)")
    print("  - pose_*.png                   (various poses)")
    print("  - topdown_view.png             (bird's eye view)")
    print("  - debug_combined.png           (combined debug)")


if __name__ == '__main__':
    main()
