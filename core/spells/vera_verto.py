"""
Vera Verto spell implementation - transforms objects with magical effects.
"""
import cv2
import math
import os
import numpy as np
from typing import Optional, Tuple
from .base import BaseSpell

class VeraVertoSpell(BaseSpell):
    """Vera Verto spell - transforms objects with simple smoke effect."""
    
    def __init__(self, frame_width: int, frame_height: int):
        super().__init__(frame_width, frame_height)
        self.state = 'idle'  # idle, ready, transforming, transformed
        self.transformation_progress = 0.0  # 0.0 to 1.0
        self.transformation_duration = 1.5  # seconds (faster)
        self.start_time = None
        
        # Object positions and size
        self.source_object_pos = None
        self.target_object_pos = None
        self.object_size = 300  # Base size for objects (2x larger)
        self.object_radius = 150  # Touch detection radius (2x larger)
        
        # Load images
        self.bird_image = None
        self.water_glass_image = None
        self._load_images()
        
        # Cached resized images
        self._cached_bird = None
        self._cached_water_glass = None
        self._cached_bird_size = None
        self._cached_water_glass_size = None
        
        # Simple smoke effect (only when transforming)
        self.smoke_particles = []
        self.max_smoke_particles = 15  # Reduced for performance
        
        # Touch detection
        self.wand_touched = False
        self.voice_verified = False  # Flag when voice is verified
        self.touch_threshold = 150  # pixels (2x larger to match object size)
        
        # Transformation state
        self._ready_for_display = False
    
    def _load_images(self):
        """Load bird and water glass images."""
        # Load bird image (source)
        bird_path = os.path.join(os.getcwd(), "assets", "images", "bird.png")
        self.bird_image = cv2.imread(bird_path, cv2.IMREAD_UNCHANGED)
        if self.bird_image is None:
            print(f"Warning: Could not load bird from {bird_path}")
        else:
            print(f"Loaded bird image: {self.bird_image.shape}")
        
        # Load water glass image (target)
        glass_path = os.path.join(os.getcwd(), "assets", "images", "water_glass.png")
        self.water_glass_image = cv2.imread(glass_path, cv2.IMREAD_UNCHANGED)
        if self.water_glass_image is None:
            print(f"Warning: Could not load water glass from {glass_path}")
        else:
            print(f"Loaded water glass image: {self.water_glass_image.shape}")
    
    def setup_scene(self):
        """Setup scene for Vera Verto - show object ready for transformation."""
        self.animation_time = 0.0
        self.state = 'ready'
        self.transformation_progress = 0.0
        self.start_time = None
        self.wand_touched = False
        self.voice_verified = False
        
        # Position object below center (further down from center)
        center_x = self.frame_width // 2
        center_y = self.frame_height // 2 + 200
        self.source_object_pos = (center_x, center_y)
        self.target_object_pos = (center_x, center_y)
        
        self.active = True
        self._ready_for_display = True
        
        # Clear smoke particles
        self.smoke_particles = []
        
        # Invalidate cache to force resize
        self._cached_bird = None
        self._cached_water_glass = None
        self._cached_bird_size = None
        self._cached_water_glass_size = None
    
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Vera Verto transformation - mark voice as verified."""
        if self.state == 'ready':
            self.voice_verified = True
            # Check if wand is already touching (transformation will start in update if both conditions met)
    
    def _init_smoke(self):
        """Initialize simple smoke particles (only when transforming)."""
        if not self.source_object_pos:
            return
        
        self.smoke_particles = []
        obj_x, obj_y = self.source_object_pos
        
        for _ in range(self.max_smoke_particles):
            angle = np.random.uniform(0, 2 * math.pi)
            speed = np.random.uniform(20, 40)
            self.smoke_particles.append({
                'x': float(obj_x),
                'y': float(obj_y),
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle) - 10,  # Upward bias
                'size': np.random.uniform(8, 20),
                'alpha': np.random.uniform(0.4, 0.8),
                'life': np.random.uniform(0.8, 1.5)
            })
    
    def _check_wand_touch(self, wand_pos: Optional[Tuple[float, float]]) -> bool:
        """Check if wand is touching the object."""
        if not wand_pos or not self.source_object_pos:
            return False
        
        # Convert normalized to pixel coordinates
        if wand_pos[0] <= 1.0 and wand_pos[1] <= 1.0:
            wand_x = int(wand_pos[0] * self.frame_width)
            wand_y = int(wand_pos[1] * self.frame_height)
        else:
            wand_x, wand_y = int(wand_pos[0]), int(wand_pos[1])
        
        obj_x, obj_y = self.source_object_pos
        
        # Check distance
        distance = math.sqrt((wand_x - obj_x) ** 2 + (wand_y - obj_y) ** 2)
        return distance <= self.touch_threshold
    
    def deactivate(self):
        """Deactivate Vera Verto spell."""
        self.active = False
        self.state = 'idle'
        self.transformation_progress = 0.0
        self._ready_for_display = False
        self.wand_touched = False
        self.voice_verified = False
        self.smoke_particles = []
    
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Vera Verto animation."""
        if not self.active:
            return
        
        self.animation_time += dt
        
        # Check if wand touches object (only in ready state)
        if self.state == 'ready':
            self.wand_touched = self._check_wand_touch(finger_pos)
            
            # Start transformation if both voice verified AND wand touched
            if self.voice_verified and self.wand_touched:
                self.state = 'transforming'
                self.start_time = self.animation_time
                self.transformation_progress = 0.0
                # Initialize smoke particles
                self._init_smoke()
        
        # Update transformation
        if self.state == 'transforming':
            if self.start_time is not None:
                elapsed = self.animation_time - self.start_time
                self.transformation_progress = min(1.0, elapsed / self.transformation_duration)
                
                if self.transformation_progress >= 1.0:
                    self.state = 'transformed'
            
            # Update smoke particles (only during transformation)
            self._update_smoke(dt)
    
    def _update_smoke(self, dt: float):
        """Update simple smoke particles (only during transformation)."""
        if not self.source_object_pos:
            return
        
        obj_x, obj_y = self.source_object_pos
        
        # Update existing particles
        for particle in self.smoke_particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt
            particle['alpha'] *= 0.98  # Fade out
            particle['size'] += 5 * dt  # Expand
            
            # Remove dead particles
            if particle['life'] <= 0 or particle['alpha'] < 0.1:
                self.smoke_particles.remove(particle)
        
        # Add new particles (up to max)
        if len(self.smoke_particles) < self.max_smoke_particles and self.transformation_progress < 0.8:
            angle = np.random.uniform(0, 2 * math.pi)
            speed = np.random.uniform(20, 40)
            self.smoke_particles.append({
                'x': float(obj_x),
                'y': float(obj_y),
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle) - 10,
                'size': np.random.uniform(8, 15),
                'alpha': np.random.uniform(0.4, 0.8),
                'life': np.random.uniform(0.8, 1.5)
            })
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Vera Verto transformation effects - simple and performant."""
        if (not self._ready_for_display and not self.active) or not self.source_object_pos:
            return frame
        
        # Draw source object (before transformation)
        if self.state in ['ready', 'transforming']:
            frame = self._draw_source_object(frame)
        
        # Draw smoke effect (only during transformation)
        if self.state == 'transforming':
            frame = self._draw_smoke(frame)
            # Show partial transformation
            frame = self._draw_partial_transformation(frame)
        
        # Draw target object (after transformation)
        if self.state == 'transformed':
            frame = self._draw_target_object(frame)
        
        return frame
    
    def _draw_smoke(self, frame: np.ndarray) -> np.ndarray:
        """Draw simple smoke particles (only during transformation)."""
        for particle in self.smoke_particles:
            x, y = int(particle['x']), int(particle['y'])
            size = int(particle['size'])
            alpha = particle['alpha']
            
            # Simple smoke circle (gray/white)
            color = (200, 200, 200)  # Light gray
            cv2.circle(frame, (x, y), size, color, -1)
            # Add slight transparency effect with darker outline
            cv2.circle(frame, (x, y), size, (150, 150, 150), 1)
        
        return frame
    
    def _get_resized_bird(self) -> Optional[np.ndarray]:
        """Get resized bird image (cached for performance)."""
        if self.bird_image is None:
            return None
        
        # Calculate current size with transformation progress
        scale_factor = 1.0 - self.transformation_progress * 0.3
        current_target_size = int(self.object_size * scale_factor)
        
        # Cache base size
        cache_key = self.object_size
        
        if self._cached_bird is None or self._cached_bird_size != cache_key:
            # Resize maintaining aspect ratio to base size
            h, w = self.bird_image.shape[:2]
            aspect = w / h if h > 0 else 1.0
            
            if w > h:
                new_w = self.object_size
                new_h = int(self.object_size / aspect)
            else:
                new_h = self.object_size
                new_w = int(self.object_size * aspect)
            
            self._cached_bird = cv2.resize(self.bird_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self._cached_bird_size = cache_key
        
        # Resize from cache to current target size (only if scale changed significantly)
        cached_h, cached_w = self._cached_bird.shape[:2]
        target_w = int(cached_w * scale_factor)
        target_h = int(cached_h * scale_factor)
        
        if abs(cached_w - target_w) > 2 or abs(cached_h - target_h) > 2:
            return cv2.resize(self._cached_bird, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        return self._cached_bird
    
    def _get_resized_water_glass(self) -> Optional[np.ndarray]:
        """Get resized water glass image (cached for performance)."""
        if self.water_glass_image is None:
            return None
        
        target_size = self.object_size
        current_size = (target_size, target_size)
        
        if self._cached_water_glass is not None and self._cached_water_glass_size == current_size:
            return self._cached_water_glass
        
        # Resize maintaining aspect ratio
        h, w = self.water_glass_image.shape[:2]
        aspect = w / h if h > 0 else 1.0
        
        if w > h:
            new_w = target_size
            new_h = int(target_size / aspect)
        else:
            new_h = target_size
            new_w = int(target_size * aspect)
        
        self._cached_water_glass = cv2.resize(self.water_glass_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        self._cached_water_glass_size = current_size
        return self._cached_water_glass
    
    def _overlay_image_alpha(self, background: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
        """Overlay image with alpha channel."""
        bg_h, bg_w = background.shape[:2]
        ov_h, ov_w = overlay.shape[:2]
        
        # Calculate center position
        x = x - ov_w // 2
        y = y - ov_h // 2
        
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
    
    def _draw_source_object(self, frame: np.ndarray) -> np.ndarray:
        """Draw source object (bird image)."""
        if self.bird_image is None or not self.source_object_pos:
            return frame
        
        x, y = self.source_object_pos
        resized_bird = self._get_resized_bird()
        
        if resized_bird is not None:
            # Fade out during transformation
            opacity = 1.0 - self.transformation_progress * 0.7
            if opacity > 0:
                # Create temporary overlay with opacity
                if resized_bird.shape[2] == 4:
                    # Has alpha channel - multiply alpha
                    overlay = resized_bird.copy()
                    overlay[:, :, 3] = (overlay[:, :, 3] * opacity).astype(np.uint8)
                    frame = self._overlay_image_alpha(frame, overlay, x, y)
                else:
                    # No alpha - blend directly
                    frame = self._overlay_image_alpha(frame, resized_bird, x, y)
        
        return frame
    
    def _draw_target_object(self, frame: np.ndarray) -> np.ndarray:
        """Draw target object (water glass image)."""
        if self.water_glass_image is None or not self.target_object_pos:
            return frame
        
        x, y = self.target_object_pos
        resized_glass = self._get_resized_water_glass()
        
        if resized_glass is not None:
            frame = self._overlay_image_alpha(frame, resized_glass, x, y)
        
        return frame
    
    def _draw_partial_transformation(self, frame: np.ndarray) -> np.ndarray:
        """Draw partial transformation (morphing between bird and water glass)."""
        if self.bird_image is None or self.water_glass_image is None:
            return frame
        
        source_x, source_y = self.source_object_pos
        target_x, target_y = self.target_object_pos
        
        # Current position (morphing)
        current_x = int(source_x + (target_x - source_x) * self.transformation_progress)
        current_y = int(source_y + (target_y - source_y) * self.transformation_progress)
        
        # Blend between bird and water glass
        bird_opacity = 1.0 - self.transformation_progress
        glass_opacity = self.transformation_progress
        
        # Draw bird (fading out)
        if bird_opacity > 0.1:
            resized_bird = self._get_resized_bird()
            if resized_bird is not None:
                if resized_bird.shape[2] == 4:
                    overlay = resized_bird.copy()
                    overlay[:, :, 3] = (overlay[:, :, 3] * bird_opacity).astype(np.uint8)
                    frame = self._overlay_image_alpha(frame, overlay, current_x, current_y)
                else:
                    frame = self._overlay_image_alpha(frame, resized_bird, current_x, current_y)
        
        # Draw water glass (fading in)
        if glass_opacity > 0.1:
            resized_glass = self._get_resized_water_glass()
            if resized_glass is not None:
                if resized_glass.shape[2] == 4:
                    overlay = resized_glass.copy()
                    overlay[:, :, 3] = (overlay[:, :, 3] * glass_opacity).astype(np.uint8)
                    frame = self._overlay_image_alpha(frame, overlay, current_x, current_y)
                else:
                    frame = self._overlay_image_alpha(frame, resized_glass, current_x, current_y)
        
        return frame
