"""
Vera Verto spell implementation - transforms objects with magical effects.
"""
import cv2
import os
import numpy as np
from typing import Optional, Tuple
from .base import BaseSpell

class VeraVertoSpell(BaseSpell):
    """Vera Verto spell - transforms objects with video smoke effect."""
    
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
        
        # Smoke video effect (using actual video frames)
        self.smoke_video_frames = []
        self.smoke_video_path = os.path.join(os.getcwd(), "assets", "videos", "smoke_video.mov")
        # Cache for resized smoke frames (performance optimization)
        self._cached_smoke_frame_index = -1
        self._cached_smoke_size = None
        self._cached_resized_smoke = None
        self._load_smoke_video()
        
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
    
    def _load_smoke_video(self):
        """Load smoke video and extract frames with optimized processing."""
        if not os.path.exists(self.smoke_video_path):
            print(f"Warning: Smoke video not found at {self.smoke_video_path}")
            return
        
        cap = cv2.VideoCapture(self.smoke_video_path)
        if not cap.isOpened():
            print(f"Warning: Could not open smoke video at {self.smoke_video_path}")
            return
        
        # Get video properties for optimization
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # Downscale to max 800px for performance (maintain aspect ratio)
        max_dimension = 800
        if max(original_width, original_height) > max_dimension:
            scale = max_dimension / max(original_width, original_height)
            target_w = int(original_width * scale)
            target_h = int(original_height * scale)
        else:
            target_w, target_h = original_width, original_height
        
        self.smoke_video_frames = []
        frame_count = 0
        
        # Process first frame to detect background type (performance: only check once)
        ret, first_frame = cap.read()
        if ret:
            gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            is_white_bg = avg_brightness > 127
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Downscale frame for performance
            if frame.shape[1] != target_w or frame.shape[0] != target_h:
                frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
            
            # Convert BGR to BGRA (add alpha channel)
            if frame.shape[2] == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                alpha = 255 - gray if is_white_bg else gray
                alpha = cv2.equalizeHist(alpha)
                frame_bgra = cv2.merge([frame[:, :, 0], frame[:, :, 1], frame[:, :, 2], alpha])
            else:
                frame_bgra = frame
            
            self.smoke_video_frames.append(frame_bgra)
            frame_count += 1
        
        cap.release()
        print(f"Loaded {frame_count} frames from smoke video (downscaled to {target_w}x{target_h})")
        
        if len(self.smoke_video_frames) == 0:
            print(f"Warning: No frames extracted from smoke video")
    
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
        
        # Invalidate caches
        self._cached_bird = None
        self._cached_water_glass = None
        self._cached_bird_size = None
        self._cached_water_glass_size = None
        self._cached_smoke_frame_index = -1
        self._cached_smoke_size = None
        self._cached_resized_smoke = None
    
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Vera Verto transformation - mark voice as verified."""
        if self.state == 'ready':
            self.voice_verified = True
            # Check if wand is already touching (transformation will start in update if both conditions met)
    
    
    def _check_wand_touch(self, wand_pos: Optional[Tuple[float, float]]) -> bool:
        """Check if wand is touching the object (optimized: no sqrt)."""
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
        dx, dy = wand_x - obj_x, wand_y - obj_y
        distance_sq = dx * dx + dy * dy
        threshold_sq = self.touch_threshold * self.touch_threshold
        return distance_sq <= threshold_sq
    
    def deactivate(self):
        """Deactivate Vera Verto spell."""
        self.active = False
        self.state = 'idle'
        self.transformation_progress = 0.0
        self._ready_for_display = False
        self.wand_touched = False
        self.voice_verified = False
    
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
        
        # Update transformation
        if self.state == 'transforming':
            if self.start_time is not None:
                elapsed = self.animation_time - self.start_time
                self.transformation_progress = min(1.0, elapsed / self.transformation_duration)
                
                if self.transformation_progress >= 1.0:
                    self.state = 'transformed'
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Vera Verto transformation effects."""
        if (not self._ready_for_display and not self.active) or not self.source_object_pos:
            return frame

        if self.state in ['ready', 'transforming']:
            frame = self._draw_source_object(frame)

        if self.state == 'transforming':
            frame = self._draw_smoke(frame)
            if self.transformation_progress > 0.7:
                glass_opacity = (self.transformation_progress - 0.7) / 0.3
                frame = self._draw_target_object(frame, opacity=glass_opacity)
        if self.state == 'transformed':
            frame = self._draw_target_object(frame)
        
        return frame
    
    def _draw_smoke(self, frame: np.ndarray) -> np.ndarray:
        """Draw smoke using video frames with caching for performance."""
        if not self.smoke_video_frames or not self.source_object_pos:
            return frame
        
        num_frames = len(self.smoke_video_frames)
        if num_frames == 0:
            return frame
        
        # Calculate frame index (cached if same progress)
        frame_index = self._get_smoke_frame_index(num_frames)
        smoke_frame = self.smoke_video_frames[frame_index]
        
        # Get object position and target size
        obj_x, obj_y = self.source_object_pos
        target_size = int(self.object_size * 2.5)
        target_size_tuple = (target_size, target_size)
        
        # Cache resized smoke frame (only resize when frame_index or size changes)
        if (self._cached_smoke_frame_index != frame_index or 
            self._cached_smoke_size != target_size_tuple):
            
            smoke_h, smoke_w = smoke_frame.shape[:2]
            aspect = smoke_w / smoke_h if smoke_h > 0 else 1.0
            
            if aspect > 1.0:
                new_w, new_h = target_size, int(target_size / aspect)
            else:
                new_h, new_w = target_size, int(target_size * aspect)
            
            self._cached_resized_smoke = cv2.resize(
                smoke_frame, (new_w, new_h), 
                interpolation=cv2.INTER_LINEAR
            )
            self._cached_smoke_frame_index = frame_index
            self._cached_smoke_size = target_size_tuple
        
        # Overlay cached resized smoke
        return self._overlay_image_alpha(frame, self._cached_resized_smoke, obj_x, obj_y)
    
    def _get_smoke_frame_index(self, num_frames: int) -> int:
        """Calculate smoke video frame index from transformation progress."""
        progress = self.transformation_progress
        
        if progress < 0.2:
            frame_index = int((progress / 0.2) * num_frames * 0.3)
        elif progress < 0.8:
            frame_index = int(0.3 * num_frames + ((progress - 0.2) / 0.6) * num_frames * 0.7)
        else:
            frame_index = int(num_frames * 0.7 + ((progress - 0.8) / 0.2) * num_frames * 0.3)
        
        return min(frame_index, num_frames - 1)
    
    def _get_resized_bird(self) -> Optional[np.ndarray]:
        """Get resized bird image (cached for performance)."""
        if self.bird_image is None:
            return None
        
        scale_factor = 1.0 - self.transformation_progress * 0.3
        
        # Cache base resized image
        if self._cached_bird is None or self._cached_bird_size != self.object_size:
            h, w = self.bird_image.shape[:2]
            aspect = w / h if h > 0 else 1.0
            new_w = self.object_size if w > h else int(self.object_size * aspect)
            new_h = int(self.object_size / aspect) if w > h else self.object_size
            
            self._cached_bird = cv2.resize(
                self.bird_image, (new_w, new_h), 
                interpolation=cv2.INTER_AREA
            )
            self._cached_bird_size = self.object_size
        
        # Scale from cache if needed
        if abs(scale_factor - 1.0) > 0.01:
            cached_h, cached_w = self._cached_bird.shape[:2]
            return cv2.resize(
                self._cached_bird, 
                (int(cached_w * scale_factor), int(cached_h * scale_factor)),
                interpolation=cv2.INTER_AREA
            )
        
        return self._cached_bird
    
    def _get_resized_water_glass(self) -> Optional[np.ndarray]:
        """Get resized water glass image (cached for performance)."""
        if self.water_glass_image is None:
            return None
        
        if self._cached_water_glass is not None and self._cached_water_glass_size == self.object_size:
            return self._cached_water_glass
        
        # Resize maintaining aspect ratio
        h, w = self.water_glass_image.shape[:2]
        aspect = w / h if h > 0 else 1.0
        new_w = self.object_size if w > h else int(self.object_size * aspect)
        new_h = int(self.object_size / aspect) if w > h else self.object_size
        
        self._cached_water_glass = cv2.resize(
            self.water_glass_image, (new_w, new_h), 
            interpolation=cv2.INTER_AREA
        )
        self._cached_water_glass_size = self.object_size
        return self._cached_water_glass
    
    def _overlay_image_alpha(self, background: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
        """Overlay image with alpha channel (optimized)."""
        bg_h, bg_w = background.shape[:2]
        ov_h, ov_w = overlay.shape[:2]
        
        # Calculate center position and bounds
        x1 = max(0, x - ov_w // 2)
        y1 = max(0, y - ov_h // 2)
        x2 = min(bg_w, x1 + ov_w)
        y2 = min(bg_h, y1 + ov_h)
        
        # Early exit if completely outside
        if x1 >= bg_w or y1 >= bg_h or x2 <= 0 or y2 <= 0:
            return background
        
        # Calculate crop regions
        ov_x1, ov_y1 = x1 - (x - ov_w // 2), y1 - (y - ov_h // 2)
        ov_x2, ov_y2 = ov_x1 + (x2 - x1), ov_y1 + (y2 - y1)
        
        # Crop overlay
        overlay_crop = overlay[ov_y1:ov_y2, ov_x1:ov_x2]
        bg_roi = background[y1:y2, x1:x2]
        
        # Alpha blending (optimized)
        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3:4].astype(np.float32) / 255.0
            bg_roi[:] = (alpha * overlay_crop[:, :, :3] + (1 - alpha) * bg_roi).astype(np.uint8)
        else:
            bg_roi[:] = overlay_crop
        
        return background
    
    def _draw_source_object(self, frame: np.ndarray) -> np.ndarray:
        """Draw source object (bird image) with fade out."""
        if self.bird_image is None or not self.source_object_pos:
            return frame
        
        resized_bird = self._get_resized_bird()
        if resized_bird is None:
            return frame
        
        # Calculate opacity (fade out in first 30% of transformation)
        opacity = max(0.0, 1.0 - (self.transformation_progress / 0.3)) if self.state == 'transforming' else 1.0
        
        if opacity <= 0:
            return frame
        
        # Apply opacity to alpha channel
        if resized_bird.shape[2] == 4:
            overlay = resized_bird.copy()
            overlay[:, :, 3] = (overlay[:, :, 3] * opacity).astype(np.uint8)
        else:
            overlay = resized_bird
        
        return self._overlay_image_alpha(frame, overlay, *self.source_object_pos)
    
    def _draw_target_object(self, frame: np.ndarray, opacity: float = 1.0) -> np.ndarray:
        """Draw target object (water glass image) with optional opacity."""
        if self.water_glass_image is None or not self.target_object_pos:
            return frame
        
        resized_glass = self._get_resized_water_glass()
        if resized_glass is None:
            return frame
        
        # Apply opacity if needed
        if opacity < 1.0:
            if resized_glass.shape[2] == 4:
                overlay = resized_glass.copy()
                overlay[:, :, 3] = (overlay[:, :, 3] * opacity).astype(np.uint8)
            else:
                overlay = np.zeros((*resized_glass.shape[:2], 4), dtype=np.uint8)
                overlay[:, :, :3] = resized_glass
                overlay[:, :, 3] = (255 * opacity).astype(np.uint8)
        else:
            overlay = resized_glass
        
        return self._overlay_image_alpha(frame, overlay, *self.target_object_pos)
