"""
interactive_demo.py - Manual control demo with combined view

Use arrow keys to drive the robot around and see both the camera
view and the top-down map.

Controls:
    Up Arrow    - Drive forward
    Down Arrow  - Drive backward
    Left Arrow  - Turn left
    Right Arrow - Turn right
    Space       - Stop
    R           - Reset position
    1-4         - Load different scenarios
    Q / Esc     - Quit
"""

import cv2
import numpy as np

from gopigo_sim import EasyGoPiGo3, load_scenario, World
from gopigo_sim.viz import draw_topdown_view


def create_display(gpg, status_text=""):
    """Create combined camera + top-down display."""
    frame = gpg.capture_frame()
    sim = gpg._sim
    
    # Create top-down view matching camera height
    topdown = draw_topdown_view(sim.world, sim.robot, size=frame.shape[0])
    
    # Add status text
    cv2.putText(frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Add labels
    cv2.putText(frame, "Camera View [Arrows=drive, R=reset, Q=quit]", 
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(topdown, "Top-Down View [1-4=scenarios]", 
                (10, topdown.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Combine side by side
    return np.hstack([frame, topdown])


def main():
    print("=" * 50)
    print("GoPiGo3 Interactive Demo")
    print("=" * 50)
    print()
    print("Controls:")
    print("  Arrow Keys - Drive robot")
    print("  Space      - Stop")
    print("  R          - Reset position")
    print("  1          - Simple gate scenario")
    print("  2          - Narrow gate scenario")
    print("  3          - Slalom course")
    print("  4          - Random pillars")
    print("  Q / Esc    - Quit")
    print()
    
    # Start with simple gate
    gpg = EasyGoPiGo3(scenario='simple_gate')
    gpg.set_speed(250)
    
    status = "Ready - use arrow keys to drive"
    current_scenario = "simple_gate"
    
    cv2.namedWindow('GoPiGo3 Simulator', cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # Show display
            display = create_display(gpg, f"[{current_scenario}] {status}")
            cv2.imshow('GoPiGo3 Simulator', display)
            
            # Handle keyboard (waitKey returns -1 if no key)
            key = cv2.waitKey(30) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or Esc
                break
            elif key == ord('r'):
                gpg.reset()
                status = "Position reset"
            elif key == ord(' '):
                gpg.stop()
                status = "Stopped"
            elif key == 82:  # Up arrow
                gpg.forward()
                status = "Forward"
            elif key == 84:  # Down arrow
                gpg.backward()
                status = "Backward"
            elif key == 81:  # Left arrow
                gpg.left()
                status = "Turning left"
            elif key == 83:  # Right arrow
                gpg.right()
                status = "Turning right"
            elif key == ord('1'):
                gpg.close()
                gpg = EasyGoPiGo3(scenario='simple_gate')
                gpg.set_speed(250)
                current_scenario = "simple_gate"
                status = "Loaded simple gate"
            elif key == ord('2'):
                gpg.close()
                gpg = EasyGoPiGo3(scenario='narrow_gate')
                gpg.set_speed(250)
                current_scenario = "narrow_gate"
                status = "Loaded narrow gate"
            elif key == ord('3'):
                gpg.close()
                gpg = EasyGoPiGo3(scenario='slalom')
                gpg.set_speed(250)
                current_scenario = "slalom"
                status = "Loaded slalom course"
            elif key == ord('4'):
                gpg.close()
                world = World.from_seed(np.random.randint(10000), num_pillars=6)
                gpg = EasyGoPiGo3(world=world)
                gpg.set_speed(250)
                current_scenario = "random"
                status = "Loaded random pillars"
                
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C")
    finally:
        gpg.stop()
        gpg.close()
        cv2.destroyAllWindows()
        print("Goodbye!")


if __name__ == '__main__':
    main()
