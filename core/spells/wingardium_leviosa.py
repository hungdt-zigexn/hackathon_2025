"""
Wingardium Leviosa spell implementation - levitates and moves objects.
"""
import cv2
import math
import os
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
        self._load_hammer()
    
    def _load_hammer(self):
        """Load and prepare Thor hammer image."""
        hammer_path = os.path.join(os.getcwd(), "assets", "images", "thor_hammer.png")
        self.hammer_image = cv2.imread(hammer_path, cv2.IMREAD_UNCHANGED)
        if self.hammer_image is None:
            print(f"Warning: Could not load hammer from {hammer_path}")
            self.hammer_image = None
        else:
            self.hammer_image = cv2.flip(self.hammer_image, 0)  # Flip upside down
            print(f"Loaded Thor hammer: {self.hammer_image.shape}")
    
    def _calculate_hammer_size(self) -> Tuple[int, int]:
        """Calculate hammer width and height based on frame size."""
        if self.hammer_image is None:
            return 0, 0
        
        base_size = min(self.frame_width, self.frame_height) * 0.45
        hammer_h, hammer_w = self.hammer_image.shape[:2]
        aspect_ratio = hammer_w / hammer_h if hammer_h > 0 else 1.0
        
        if hammer_w > hammer_h:
            return int(base_size), int(base_size / aspect_ratio)
        return int(base_size * aspect_ratio), int(base_size)
    
    def _calculate_grounded_position(self) -> Tuple[int, int]:
        """Calculate position for grounded hammer."""
        center_x = self.frame_width // 2
        if self.hammer_image is None:
            return center_x, self.frame_height - 50
        
        _, hammer_height = self._calculate_hammer_size()
        return center_x, self.frame_height - hammer_height // 2 - 20
    
    def setup_scene(self):
        """Setup scene for Wingardium Leviosa."""
        self.animation_time = 0.0
        self.state = 'grounded'
        self.object_pos = self._calculate_grounded_position()
        self.hover_offset = 0.0
        self.reached_target = False
        self.active = True
    
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
    
    def _to_pixel_coords(self, finger_pos: Optional[Tuple[float, float]]) -> Optional[Tuple[int, int]]:
        """Convert normalized finger position to pixel coordinates."""
        if not finger_pos:
            return None
        
        if finger_pos[0] <= 1.0 and finger_pos[1] <= 1.0:
            return (int(finger_pos[0] * self.frame_width), int(finger_pos[1] * self.frame_height))
        return (int(finger_pos[0]), int(finger_pos[1]))
    
    def _update_floating(self, dt: float, finger_pixel: Optional[Tuple[int, int]]):
        """Update floating state animation."""
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
            current_x = self.frame_width // 2
        # Phase 2: Follow finger tip
        elif self.follow_finger and finger_pixel:
            target_x = max(box_margin, min(finger_pixel[0], self.frame_width - box_margin))
            target_y_pos = max(box_margin, min(finger_pixel[1], self.frame_height - box_margin))
            current_x += (target_x - current_x) * lerp_factor
            current_y += (target_y_pos - current_y) * lerp_factor

        self.hover_offset = math.sin(self.animation_time * 2.0) * 10
        self.object_pos = (int(current_x), int(current_y))
    
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Wingardium Leviosa animation."""
        if not self.active or not self.object_pos:
            return
        
        self.animation_time += dt
        finger_pixel = self._to_pixel_coords(finger_pos)
        
        if self.state == 'floating':
            self._update_floating(dt, finger_pixel)
        elif self.state == 'grounded':
            self.object_pos = self._calculate_grounded_position()
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Wingardium Leviosa object (Thor hammer)."""
        if not self.active or not self.object_pos or self.hammer_image is None:
            return frame
        
        x, y = int(self.object_pos[0]), int(self.object_pos[1])
        if self.state == 'floating':
            y += int(self.hover_offset)
        
        hammer_width, hammer_height = self._calculate_hammer_size()
        resized_hammer = cv2.resize(self.hammer_image, (hammer_width, hammer_height), interpolation=cv2.INTER_AREA)
        return self._overlay_image_alpha(frame, resized_hammer, x - hammer_width // 2, y - hammer_height // 2)
    
    def _overlay_image_alpha(self, background: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
        """Overlay image with alpha channel."""
        bg_h, bg_w = background.shape[:2]
        ov_h, ov_w = overlay.shape[:2]
        
        # Clip overlay to fit within background
        if x >= bg_w or y >= bg_h or x + ov_w <= 0 or y + ov_h <= 0:
            return background
        
        # Calculate valid overlay region
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(bg_w, x + ov_w)
        y2 = min(bg_h, y + ov_h)
        
        # Calculate overlay crop
        ov_x1 = x1 - x
        ov_y1 = y1 - y
        ov_x2 = ov_x1 + (x2 - x1)
        ov_y2 = ov_y1 + (y2 - y1)
        
        # Crop overlay
        overlay_crop = overlay[ov_y1:ov_y2, ov_x1:ov_x2]
        
        if overlay_crop.shape[2] == 4:  # Has alpha channel
            alpha = overlay_crop[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)
            
            # Blend
            background[y1:y2, x1:x2] = (
                alpha * overlay_crop[:, :, :3] +
                (1 - alpha) * background[y1:y2, x1:x2]
            ).astype(np.uint8)
        else:
            background[y1:y2, x1:x2] = overlay_crop
        
        return background
