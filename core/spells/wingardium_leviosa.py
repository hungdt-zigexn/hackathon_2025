"""
Wingardium Leviosa spell implementation - levitates and moves objects.
"""
import cv2
import math
from typing import Optional, Tuple
import numpy as np
from .base import BaseSpell


class WingardiumLeviosaSpell(BaseSpell):
    """Wingardium Leviosa spell - levitates and moves objects."""
    
    def __init__(self, frame_width: int, frame_height: int):
        super().__init__(frame_width, frame_height)
        self.state = 'idle'  # idle, grounded, floating
        self.object_pos = None
        self.hover_offset = 0.0
        self.follow_finger = False
        self.reached_target = False
    
    def setup_scene(self):
        """Setup scene for Wingardium Leviosa."""
        self.animation_time = 0.0
        self.state = 'grounded'
        center_x = self.frame_width // 2
        bottom_y = self.frame_height - 50
        self.object_pos = (center_x, bottom_y)
        self.hover_offset = 0.0
        self.reached_target = False
        self.active = True  # Show grounded object
    
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Wingardium Leviosa spell."""
        self.state = 'floating'
        self.follow_finger = True
        self.active = True
        if self.state == 'idle':
            self.animation_time = 0.0
    
    def deactivate(self):
        """Deactivate Wingardium Leviosa spell."""
        self.active = False
        self.state = 'idle'
    
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Wingardium Leviosa animation."""
        if not self.active or not self.object_pos:
            return
        
        self.animation_time += dt
        
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
        
        if self.state == 'floating':
            target_y = self.frame_height // 3
            current_x, current_y = self.object_pos
            box_margin, rise_speed, lerp_factor = 30, 100 * dt, 0.15

            # Phase 1: Rise to target height
            if not self.reached_target:
                if current_y > target_y:
                    current_y = max(target_y, current_y - rise_speed)
                if current_y <= target_y:
                    current_y = target_y
                    self.reached_target = True
                    print(f"[DEBUG] Leviosa reached target_y={target_y}")
                current_x = self.frame_width // 2

            # Phase 2: Follow finger tip after reaching target
            elif self.follow_finger and finger_pixel:
                target_x = max(box_margin, min(finger_pixel[0], self.frame_width - box_margin))
                target_y_pos = max(box_margin, min(finger_pixel[1], self.frame_height - box_margin))
                current_x += (target_x - current_x) * lerp_factor
                current_y += (target_y_pos - current_y) * lerp_factor

            # Hover animation
            self.hover_offset = math.sin(self.animation_time * 2.0) * 10
            self.object_pos = (int(current_x), int(current_y))
        
        elif self.state == 'grounded':
            # Ensure it stays at bottom (in case of resize)
            self.object_pos = (
                self.frame_width // 2,
                self.frame_height - 50
            )
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Wingardium Leviosa object (box)."""
        if not self.active or not self.object_pos:
            return frame
        
        box_size = 60
        x, y = int(self.object_pos[0]), int(self.object_pos[1])
        
        # Add hover offset if floating
        if self.state == 'floating':
            y += int(self.hover_offset)
        
        # Draw a crate-like box
        # Main box body
        top_left = (x - box_size//2, y - box_size//2)
        bottom_right = (x + box_size//2, y + box_size//2)
        
        # Fill - brown wood color
        cv2.rectangle(frame, top_left, bottom_right, (30, 70, 110), -1)
        
        # Border - lighter wood
        cv2.rectangle(frame, top_left, bottom_right, (50, 90, 130), 3)
        
        # Cross pattern
        cv2.line(frame, top_left, bottom_right, (40, 80, 120), 2)
        cv2.line(frame, (x + box_size//2, y - box_size//2), (x - box_size//2, y + box_size//2), (40, 80, 120), 2)
        
        # Inner border
        inset = 5
        cv2.rectangle(frame, (top_left[0]+inset, top_left[1]+inset), (bottom_right[0]-inset, bottom_right[1]-inset), (45, 85, 125), 1)
        
        return frame
