"""
Expecto Patronum spell implementation - draws patterns and displays patronus.
"""
import cv2
import time
import os
from typing import Optional, Tuple, List
import numpy as np
from .base import BaseSpell


class ExpectoPatronumSpell(BaseSpell):
    """Expecto Patronum spell - draws patterns and displays patronus."""
    
    def __init__(self, frame_width: int, frame_height: int):
        super().__init__(frame_width, frame_height)
        self.path: List[Tuple[int, int]] = []
        self.recording_start_time: Optional[float] = None
        self.identification_pending: bool = False
        self.identified_object: Optional[str] = None
        self.image: Optional[np.ndarray] = None
        self.model_rotation: float = 0.0
        self.model_position: Optional[Tuple[int, int]] = None
    
    def setup_scene(self):
        """Setup scene for Expecto Patronum."""
        self.animation_time = 0.0
        self.recording_start_time = None
        self.path = []
        self.identified_object = None
        self.image = None
        self.active = False
    
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Expecto Patronum spell."""
        self.path = []
        self.recording_start_time = time.time()
        self.identification_pending = False
        self.identified_object = None
        self.image = None
        self.model_rotation = 0.0
        self.model_position = None
        self.active = True
        self.animation_time = 0.0
    
    def deactivate(self):
        """Deactivate Expecto Patronum spell."""
        self.active = False
    
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Expecto Patronum animation."""
        if not self.active:
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
        
        if self.recording_start_time is not None:
            elapsed = time.time() - self.recording_start_time

            # Recording phase: first 5 seconds
            if elapsed < 5.0:
                if finger_pixel:
                    self.path.append(finger_pixel)
            # After 5 seconds, trigger identification
            elif not self.identification_pending and self.identified_object is None:
                self.identification_pending = True
                # Set position for model display
                if self.path:
                    xs = [p[0] for p in self.path]
                    ys = [p[1] for p in self.path]
                    if xs and ys:
                        self.model_position = (
                            int(sum(xs) / len(xs)),
                            int(sum(ys) / len(ys))
                        )
                else:
                    self.model_position = finger_pixel if finger_pixel else (self.frame_width // 2, self.frame_height // 2)

        # Display phase: animate model rotation
        if self.identified_object and self.image is not None:
            self.model_rotation += dt * 1.0
    
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """Draw Expecto Patronum effects."""
        if not self.active:
            return frame
        
        if self.recording_start_time is not None:
            elapsed = time.time() - self.recording_start_time

            # Recording phase: draw path
            if elapsed < 5.0:
                if len(self.path) > 1:
                    pts = np.array(self.path, np.int32)
                    cv2.polylines(frame, [pts], False, (255, 200, 150), 3, cv2.LINE_AA)
                    if self.path:
                        cv2.circle(frame, self.path[-1], 5, (255, 200, 150), -1)

            # Display phase: render image
            if self.identified_object and self.image is not None and self.model_position:
                x, y = self.model_position
                h, w = self.image.shape[:2]

                top_left_x = int(x - w / 2)
                top_left_y = int(y - h / 2)

                self._overlay_image(frame, self.image, top_left_x, top_left_y)

                # Draw object name
                text = self.identified_object.capitalize()
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.5
                thickness = 3
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

                text_x = int(x - text_size[0] / 2)
                text_y = int(y - h / 2 - 20)

                cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
                cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
        return frame
    
    def load_model(self, object_name: str) -> bool:
        """Load a 2D image for the patronus."""
        extensions = ['.png', '.jpg', '.jpeg']
        image_path = None

        for ext in extensions:
            path = os.path.join(os.getcwd(), "assets", "images", f"{object_name}{ext}")
            if os.path.exists(path):
                image_path = path
                break

        if not image_path:
            print(f"Image file not found for object: {object_name}")
            return False

        try:
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                print(f"Failed to load image: {image_path}")
                return False

            # Resize to reasonable size
            h, w = image.shape[:2]
            max_dim = max(h, w)
            if max_dim > 300:
                scale = 300.0 / max_dim
                new_w = int(w * scale)
                new_h = int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

            self.image = image
            print(f"Loaded image: {object_name}")
            return True
        except Exception as e:
            print(f"Error loading image {object_name}: {e}")
            return False
    
    def _overlay_image(self, background: np.ndarray, foreground: np.ndarray, x: int, y: int) -> None:
        """Overlay a foreground image onto a background image at (x, y) handling alpha channel."""
        h_fg, w_fg = foreground.shape[:2]
        h_bg, w_bg = background.shape[:2]
        
        if x >= w_bg or y >= h_bg:
            return
            
        # Crop foreground if it goes outside background
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(w_bg, x + w_fg)
        y_end = min(h_bg, y + h_fg)
        
        # Calculate source coordinates
        fg_x_start = x_start - x
        fg_y_start = y_start - y
        fg_x_end = fg_x_start + (x_end - x_start)
        fg_y_end = fg_y_start + (y_end - y_start)
        
        if fg_x_end <= fg_x_start or fg_y_end <= fg_y_start:
            return
            
        fg_crop = foreground[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
        bg_crop = background[y_start:y_end, x_start:x_end]
        
        # Check if foreground has alpha channel
        if fg_crop.shape[2] == 4:
            alpha = fg_crop[:, :, 3] / 255.0
            alpha_inv = 1.0 - alpha
            
            for c in range(3):
                bg_crop[:, :, c] = (alpha * fg_crop[:, :, c] + alpha_inv * bg_crop[:, :, c])
        else:
            background[y_start:y_end, x_start:x_end] = fg_crop

