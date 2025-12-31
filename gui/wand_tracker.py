"""
Wand tracking processor using hand detection.
"""
from typing import Optional, Tuple
from core.hand_tracking import HandTracker


class WandTracker:
    """Handles hand detection and wand position tracking with smoothing."""
    
    def __init__(self, hand_tracker: HandTracker, smoothing_factor: float = 0.5):
        """
        Initialize wand tracker.
        
        Args:
            hand_tracker: HandTracker instance for hand detection
            smoothing_factor: Smoothing factor (0-1). Higher = more responsive, Lower = smoother
        """
        self.hand_tracker = hand_tracker
        self.smoothing_factor = smoothing_factor
        
        # Smoothing state
        self.prev_wand_tip = None
        self.prev_wand_base = None
    
    def process_frame(self, frame, frame_width: int, frame_height: int) -> Optional[Tuple[float, float]]:
        """
        Process frame and return normalized wand tip position.
        
        Args:
            frame: Input frame (BGR format)
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        
        Returns:
            Normalized wand tip position (x, y) in range [0, 1], or None if no hand detected
        """
        # Process hand tracking
        landmarks = self.hand_tracker.process_frame(frame)
        
        if not landmarks:
            # Reset smoothing if hand lost
            self.prev_wand_tip = None
            self.prev_wand_base = None
            return None
        
        # MediaPipe returns normalized coordinates (0-1)
        raw_tip_norm = self.hand_tracker.get_wand_position(landmarks)
        raw_base_norm = self.hand_tracker.get_wand_base(landmarks)
        
        # Apply smoothing to Tip
        if raw_tip_norm:
            curr_tip_x = raw_tip_norm[0] * frame_width
            curr_tip_y = raw_tip_norm[1] * frame_height
            
            if self.prev_wand_tip:
                smooth_x = curr_tip_x * self.smoothing_factor + self.prev_wand_tip[0] * (1 - self.smoothing_factor)
                smooth_y = curr_tip_y * self.smoothing_factor + self.prev_wand_tip[1] * (1 - self.smoothing_factor)
                self.prev_wand_tip = (smooth_x, smooth_y)
            else:
                self.prev_wand_tip = (curr_tip_x, curr_tip_y)
            
            wand_tip_normalized = (self.prev_wand_tip[0] / frame_width, self.prev_wand_tip[1] / frame_height)
        else:
            wand_tip_normalized = None
        
        # Apply smoothing to Base (for potential future use)
        if raw_base_norm:
            curr_base_x = raw_base_norm[0] * frame_width
            curr_base_y = raw_base_norm[1] * frame_height
            
            if self.prev_wand_base:
                smooth_x = curr_base_x * self.smoothing_factor + self.prev_wand_base[0] * (1 - self.smoothing_factor)
                smooth_y = curr_base_y * self.smoothing_factor + self.prev_wand_base[1] * (1 - self.smoothing_factor)
                self.prev_wand_base = (smooth_x, smooth_y)
            else:
                self.prev_wand_base = (curr_base_x, curr_base_y)
        else:
            self.prev_wand_base = None
        
        return wand_tip_normalized
    
    def get_wand_tip_pixel(self, frame_width: int, frame_height: int) -> Optional[Tuple[int, int]]:
        """
        Get wand tip position in pixel coordinates.
        
        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        
        Returns:
            Wand tip position (x, y) in pixels, or None if no hand detected
        """
        if self.prev_wand_tip is None:
            return None
        
        return (int(self.prev_wand_tip[0]), int(self.prev_wand_tip[1]))
    
    def get_wand_base_pixel(self, frame_width: int, frame_height: int) -> Optional[Tuple[int, int]]:
        """
        Get wand base position in pixel coordinates.
        
        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        
        Returns:
            Wand base position (x, y) in pixels, or None if no hand detected
        """
        if self.prev_wand_base is None:
            return None
        
        return (int(self.prev_wand_base[0]), int(self.prev_wand_base[1]))
    
    def reset(self):
        """Reset smoothing state."""
        self.prev_wand_tip = None
        self.prev_wand_base = None
