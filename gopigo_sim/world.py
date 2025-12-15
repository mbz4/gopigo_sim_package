"""
world.py - Defines the simulation world: pillars, boundaries, and scenarios.

The world uses a simple 2D coordinate system:
- X increases to the right
- Y increases upward (forward from robot's starting position)
- Units are in centimeters (matching real GoPiGo3 scale)
"""

from dataclasses import dataclass
from typing import List, Tuple
import random


@dataclass
class Pillar:
    """A colored vertical pillar in the world."""
    x: float              # X position in cm
    y: float              # Y position in cm  
    color: str            # 'green' or 'orange'
    radius: float = 5.0   # Pillar radius in cm
    height: float = 30.0  # Pillar height in cm (for camera rendering)
    
    # BGR colors for OpenCV rendering
    COLOR_MAP = {
        'green': (0, 255, 0),
        'orange': (0, 165, 255),
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
    }
    
    @property
    def bgr(self) -> Tuple[int, int, int]:
        """Get BGR color tuple for OpenCV."""
        return self.COLOR_MAP.get(self.color, (128, 128, 128))


@dataclass 
class World:
    """
    The simulation world containing pillars and boundaries.
    
    Coordinate system:
    - Origin (0, 0) is typically where the robot starts
    - Positive Y is "forward" from the robot's initial heading
    - Positive X is "right" from the robot's perspective
    """
    pillars: List[Pillar]
    width: float = 200.0   # World width in cm (X range: -width/2 to +width/2)
    height: float = 300.0  # World height in cm (Y range: 0 to height)
    
    def __post_init__(self):
        self._seed = None
    
    @classmethod
    def two_pillar_gate(cls, gap: float = 40.0, distance: float = 100.0,
                        left_color: str = 'green', right_color: str = 'orange') -> 'World':
        """
        Create a standard scenario: two pillars forming a gate to drive through.
        
        Args:
            gap: Distance between pillar centers in cm
            distance: How far ahead the gate is (Y position)
            left_color: Color of left pillar
            right_color: Color of right pillar
        """
        pillars = [
            Pillar(x=-gap/2, y=distance, color=left_color),
            Pillar(x=+gap/2, y=distance, color=right_color),
        ]
        return cls(pillars=pillars)
    
    @classmethod
    def slalom_course(cls, num_gates: int = 3, spacing: float = 80.0) -> 'World':
        """Create a slalom course with alternating gates."""
        pillars = []
        for i in range(num_gates):
            y = 80 + i * spacing
            offset = 30 if i % 2 == 0 else -30
            pillars.append(Pillar(x=offset - 20, y=y, color='green'))
            pillars.append(Pillar(x=offset + 20, y=y, color='orange'))
        return cls(pillars=pillars)
    
    @classmethod
    def from_seed(cls, seed: int, num_pillars: int = 4) -> 'World':
        """
        Create a deterministic random world from a seed.
        Use the same seed to replay the exact same scenario.
        """
        rng = random.Random(seed)
        colors = ['green', 'orange']
        pillars = []
        
        for _ in range(num_pillars):
            pillars.append(Pillar(
                x=rng.uniform(-80, 80),
                y=rng.uniform(50, 250),
                color=rng.choice(colors)
            ))
        
        world = cls(pillars=pillars)
        world._seed = seed
        return world
    
    def get_pillar_at(self, x: float, y: float, tolerance: float = 10.0) -> Pillar:
        """Find a pillar near the given position, or None."""
        for p in self.pillars:
            dist = ((p.x - x)**2 + (p.y - y)**2)**0.5
            if dist < tolerance:
                return p
        return None


# Pre-built scenarios for easy testing
SCENARIOS = {
    'simple_gate': lambda: World.two_pillar_gate(gap=50, distance=80),
    'narrow_gate': lambda: World.two_pillar_gate(gap=30, distance=80),
    'offset_gate': lambda: World.two_pillar_gate(gap=40, distance=100),
    'slalom': lambda: World.slalom_course(num_gates=3),
}


def load_scenario(name: str) -> World:
    """Load a pre-built scenario by name."""
    if name not in SCENARIOS:
        available = ', '.join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")
    return SCENARIOS[name]()
