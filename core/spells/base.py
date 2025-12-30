"""
Base class for spell implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class BaseSpell(ABC):
    """Base class for all spell implementations."""
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize spell.
        
        Args:
            frame_width: Width of video frame
            frame_height: Height of video frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.animation_time = 0.0
        self.active = False
    
    def update_frame_size(self, width: int, height: int):
        """Update frame dimensions."""
        self.frame_width = width
        self.frame_height = height
    
    @abstractmethod
    def setup_scene(self):
        """Setup the visual scene for the spell (before activation)."""
        pass
    
    @abstractmethod
    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate the spell effect."""
        pass
    
    @abstractmethod
    def deactivate(self):
        """Deactivate the spell."""
        pass
    
    @abstractmethod
    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """
        Update spell animations.
        
        Args:
            dt: Delta time since last update (seconds)
            finger_pos: Current finger position in normalized coordinates (0-1)
        """
        pass
    
    @abstractmethod
    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """
        Draw spell effects on frame.
        
        Args:
            frame: BGR image frame
            finger_pos: Current finger position in normalized coordinates (0-1)
            
        Returns:
            Frame with effects drawn
        """
        pass

