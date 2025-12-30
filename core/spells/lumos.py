"""
Lumos spell implementation - creates a glowing light effect.
"""
import cv2
import math
from typing import Optional, Tuple
import numpy as np
from .base import BaseSpell


class LumosSpell(BaseSpell):
    """Lumos spell - creates a glowing light at finger tip."""
    
    def __init__(self, frame_width: int, frame_height: int):
        super().__init__(frame_width, frame_height)
    
    def setup_scene(self):
        """Setup scene for Lumos."""
        self.animation_time = 0.0
        self.active = False
    
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Lumos spell."""
        self.active = True
        self.animation_time = 0.0
    
    def deactivate(self):
        """Deactivate Lumos spell."""
        self.active = False
    
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Lumos animation."""
        if self.active:
            self.animation_time += dt
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Lumos glow effect."""
        if not self.active:
            return frame
        
        # Convert finger position to pixel coordinates
        finger_pixel = None
        if finger_pos:
            if finger_pos[0] <= 1.0 and finger_pos[1] <= 1.0:
                finger_pixel = (
                    int(finger_pos[0] * self.frame_width),
                    int(finger_pos[1] * self.frame_height)
                )
            else:
                finger_pixel = (int(finger_pos[0]), int(finger_pos[1]))
        
        if finger_pixel:
            # Calculate glow radius with animation
            glow_radius = int(30 + 10 * math.sin(self.animation_time * 5.0))
            
            # Draw multiple layers for intense glow effect
            cv2.circle(frame, finger_pixel, glow_radius + 20, (255, 255, 150), -1)  # Outer glow
            cv2.circle(frame, finger_pixel, glow_radius + 10, (255, 255, 200), -1)  # Middle glow
            cv2.circle(frame, finger_pixel, glow_radius, (255, 255, 255), -1)  # Inner core
            cv2.circle(frame, finger_pixel, glow_radius + 15, (255, 255, 180), 3)  # Outer ring
        
        return frame

