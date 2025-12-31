"""
Spell engine for managing visual effects of spells.
"""
import cv2
import numpy as np
from typing import Optional, Tuple, List
from enum import Enum
import math

from .spells import LumosSpell, WingardiumLeviosaSpell, ExpectoPatronumSpell


class SpellType(Enum):
    """Types of spells available."""
    LUMOS = "Lumos"
    WINGARDIUM_LEVIOSA = "Wingardium Leviosa"
    EXPECTO_PATRONUM = "Expecto Patronum"


class SpellEngine:
    """Manages spell visual effects and animations."""
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize spell engine.
        
        Args:
            frame_width: Width of video frame
            frame_height: Height of video frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.current_spell: Optional[SpellType] = None
        self.spell_active = False
        
        # Initialize spell instances
        self.lumos = LumosSpell(frame_width, frame_height)
        self.wingardium_leviosa = WingardiumLeviosaSpell(frame_width, frame_height)
        self.expecto_patronum = ExpectoPatronumSpell(frame_width, frame_height, "assets/images/spell_guide.webp")
        
        # Current active spell instance
        self._active_spell_instance = None
    
    def _get_spell_instance(self, spell_type: SpellType):
        """Get spell instance for given type."""
        if spell_type == SpellType.LUMOS:
            return self.lumos
        elif spell_type == SpellType.WINGARDIUM_LEVIOSA:
            return self.wingardium_leviosa
        elif spell_type == SpellType.EXPECTO_PATRONUM:
            return self.expecto_patronum
        return None
    
    def setup_spell_scene(self, spell_type: SpellType):
        """
        Setup the visual scene for a spell (before activation).
        
        Args:
            spell_type: Type of spell to setup
        """
        print(f"[DEBUG] setup_spell_scene called: spell_type={spell_type}")
        self.current_spell = spell_type
        spell_instance = self._get_spell_instance(spell_type)
        
        if spell_instance:
            spell_instance.setup_scene()
            # For Wingardium Leviosa, we need spell_active=True to show the grounded object
            if spell_type == SpellType.WINGARDIUM_LEVIOSA:
                self.spell_active = True
            else:
                self.spell_active = False
    
    def activate_spell(self, spell_type: SpellType, wand_pos: Optional[Tuple[float, float]] = None):
        """
        Activate a spell effect.
        
        Args:
            spell_type: Type of spell to activate
            wand_pos: Current wand position in normalized coordinates (0-1), or None for center
        """
        print(f"[DEBUG] activate_spell called: spell_type={spell_type}, wand_pos={wand_pos}")
        self.current_spell = spell_type
        self.spell_active = True
        
        spell_instance = self._get_spell_instance(spell_type)
        if spell_instance:
            spell_instance.activate(wand_pos)
            self._active_spell_instance = spell_instance
        
        print(f"[DEBUG] Spell activated: spell_active={self.spell_active}, current_spell={self.current_spell}")
    
    def deactivate_spell(self):
        """Deactivate current spell."""
        print(f"[DEBUG] deactivate_spell called")
        self.spell_active = False
        self.current_spell = None
        
        if self._active_spell_instance:
            self._active_spell_instance.deactivate()
            self._active_spell_instance = None
    
    def update(self, dt: float, wand_pos: Optional[Tuple[float, float]] = None):
        """
        Update spell animations.
        
        Args:
            dt: Delta time since last update (seconds)
            wand_pos: Current wand position in normalized coordinates (0-1) for tracking
        """
        if not self.spell_active or self.current_spell is None:
            return
        
        spell_instance = self._get_spell_instance(self.current_spell)
        if spell_instance:
            spell_instance.update(dt, wand_pos)
    
    def update_frame_size(self, width: int, height: int):
        """Update frame dimensions."""
        self.frame_width = width
        self.frame_height = height
        
        # Update all spell instances
        self.lumos.update_frame_size(width, height)
        self.wingardium_leviosa.update_frame_size(width, height)
        self.expecto_patronum.update_frame_size(width, height)
    
    def draw_effects(self, frame: np.ndarray, wand_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        """
        Draw spell effects on frame.
        
        Args:
            frame: BGR image frame
            wand_pos: Current wand position (x, y) in normalized coordinates (0-1)
            
        Returns:
            Frame with effects drawn
        """
        if not self.spell_active or self.current_spell is None:
            return frame
        
        spell_instance = self._get_spell_instance(self.current_spell)
        if spell_instance:
            return spell_instance.draw(frame, wand_pos)
        
        return frame
    
    # Backward compatibility properties for Wingardium Leviosa
    @property
    def leviosa_state(self):
        """Get leviosa state."""
        return self.wingardium_leviosa.state
    
    @property
    def leviosa_object_pos(self):
        """Get leviosa object position."""
        return self.wingardium_leviosa.object_pos
    
    @property
    def leviosa_hover_offset(self):
        """Get leviosa hover offset."""
        return self.wingardium_leviosa.hover_offset
    
    @property
    def leviosa_follow_finger(self):
        """Get leviosa follow finger flag."""
        return self.wingardium_leviosa.follow_finger
    
    @property
    def leviosa_reached_target(self):
        """Get leviosa reached target flag."""
        return self.wingardium_leviosa.reached_target
    
    # Backward compatibility properties for Expecto Patronum
    @property
    def patronum_path(self):
        """Get patronum path."""
        return self.expecto_patronum.path
    
    @property
    def recording_start_time(self):
        """Get recording start time."""
        return self.expecto_patronum.recording_start_time
    
    @property
    def identification_pending(self):
        """Get identification pending flag."""
        return self.expecto_patronum.identification_pending
    
    @identification_pending.setter
    def identification_pending(self, value):
        """Set identification pending flag."""
        self.expecto_patronum.identification_pending = value
    
    @property
    def identified_object(self):
        """Get identified object."""
        return self.expecto_patronum.identified_object
    
    @identified_object.setter
    def identified_object(self, value):
        """Set identified object."""
        self.expecto_patronum.identified_object = value
    
    @property
    def patronum_image(self):
        """Get patronum image."""
        return self.expecto_patronum.image
    
    @property
    def patronum_model_rotation(self):
        """Get patronum model rotation."""
        return self.expecto_patronum.model_rotation
    
    @property
    def patronum_model_position(self):
        """Get patronum model position."""
        return self.expecto_patronum.model_position
    
    def load_patronum_model(self, object_name: str) -> bool:
        """
        Load a 2D image for the EXPECTO_PATRONUM spell.

        Args:
            object_name: Name of the object (ball, cat, heart, pizza, star, wand)

        Returns:
            True if image loaded successfully, False otherwise
        """
        return self.expecto_patronum.load_model(object_name)
    
    def draw_wand(self, frame: np.ndarray, wand_tip: Optional[Tuple[int, int]],
                  wand_base: Optional[Tuple[int, int]] = None) -> Tuple[np.ndarray, Optional[Tuple[int, int]]]:
        """
        Draw virtual wand on frame using programmatic drawing.
        
        Args:
            frame: BGR image frame
            wand_tip: Wand tip position (x, y) in pixel coordinates
            wand_base: Wand base position (x, y) in pixel coordinates
            
        Returns:
            Tuple of (Frame with wand drawn, visual tip position (x, y))
        """
        if wand_tip is None:
            return frame, None
        
        # Convert normalized coordinates if needed
        if wand_tip[0] <= 1.0 and wand_tip[1] <= 1.0:
            tip_pixel = (
                int(wand_tip[0] * self.frame_width),
                int(wand_tip[1] * self.frame_height)
            )
        else:
            tip_pixel = wand_tip
        
        if wand_base:
            if wand_base[0] <= 1.0 and wand_base[1] <= 1.0:
                base_pixel = (
                    int(wand_base[0] * self.frame_width),
                    int(wand_base[1] * self.frame_height)
                )
            else:
                base_pixel = wand_base
        else:
            # Default base position (slightly offset from tip)
            base_pixel = (tip_pixel[0] - 100, tip_pixel[1] + 200)
            
        # Calculate wand vector
        dx = tip_pixel[0] - base_pixel[0]
        dy = tip_pixel[1] - base_pixel[1]
        original_length = math.sqrt(dx*dx + dy*dy)
        
        if original_length < 1.0:
            return frame, None
            
        # Normalize vector
        ux = dx / original_length
        uy = dy / original_length
        
        # Extend wand length (make it visually longer)
        extended_length = original_length * 5.0
        
        # Recalculate tip pixel based on extended length
        tip_pixel = (
            int(base_pixel[0] + ux * extended_length),
            int(base_pixel[1] + uy * extended_length)
        )
        
        # Use extended length for drawing calculations
        length = extended_length
        
        # Perpendicular vector
        px = -uy
        py = ux
        
        # Wand parameters
        width_base = 30
        width_tip = 10
        
        # Calculate polygon corners
        b1x = base_pixel[0] + px * width_base
        b1y = base_pixel[1] + py * width_base
        b2x = base_pixel[0] - px * width_base
        b2y = base_pixel[1] - py * width_base
        
        t1x = tip_pixel[0] + px * width_tip
        t1y = tip_pixel[1] + py * width_tip
        t2x = tip_pixel[0] - px * width_tip
        t2y = tip_pixel[1] - py * width_tip
        
        # Create polygon points
        pts = np.array([
            [b1x, b1y],
            [t1x, t1y],
            [t2x, t2y],
            [b2x, b2y]
        ], np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Draw wand body (dark brown)
        cv2.fillPoly(frame, [pts], (30, 50, 90))
        
        # Draw wand border (lighter brown)
        cv2.polylines(frame, [pts], True, (50, 80, 120), 2, cv2.LINE_AA)
        
        # Draw handle detail
        handle_len = length * 0.25
        hx = base_pixel[0] + ux * handle_len
        hy = base_pixel[1] + uy * handle_len
        
        width_handle = width_base - ((width_base - width_tip) * 0.25)
        
        h1x = hx + px * width_handle
        h1y = hy + py * width_handle
        h2x = hx - px * width_handle
        h2y = hy - py * width_handle
        
        handle_pts = np.array([
            [b1x, b1y],
            [h1x, h1y],
            [h2x, h2y],
            [b2x, b2y]
        ], np.int32)
        handle_pts = handle_pts.reshape((-1, 1, 2))
        
        # Draw handle overlay
        cv2.fillPoly(frame, [handle_pts], (40, 70, 110))
        cv2.polylines(frame, [handle_pts], True, (60, 90, 140), 2, cv2.LINE_AA)
        
        # Draw tip highlight
        cv2.circle(frame, tip_pixel, 5, (200, 200, 200), -1)
        
        return frame, tip_pixel
