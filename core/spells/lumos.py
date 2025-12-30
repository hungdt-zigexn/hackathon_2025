"""
Lumos spell implementation - creates a premium magical glowing light effect.
"""
import cv2
import math
import time
from typing import Optional, Tuple
import numpy as np
from .base import BaseSpell


class LumosSpell(BaseSpell):
    """Lumos spell - creates a premium magical golden light effect with multi-layer aura."""

    # Animation timing constants (seconds)
    FLASH_DURATION = 0.125
    GLOW_IN_DURATION = 0.425
    FADE_OUT_DURATION = 0.5

    # Visual and behavior constants
    POSITION_SMOOTHING_FACTOR = 0.4
    MOTION_SPEED_SMOOTHING = 0.8
    BASE_RADIUS_RATIO = 1/6
    MAX_RADIUS_RATIO = 1/3
    INNER_RADIUS_RATIO = 0.35
    MID_RADIUS_RATIO = 0.75

    # Flicker behavior constants
    FLICKER_INTERVAL_MIN = 0.2
    FLICKER_INTERVAL_MAX = 0.6
    FLICKER_VARIATION_RANGE = 0.2
    FLICKER_INTENSITY_MIN = 0.9
    FLICKER_INTENSITY_MAX = 1.1

    # Motion expansion constants
    MOTION_EXPANSION_MULTIPLIER = 30

    def __init__(self, frame_width: int, frame_height: int):
        super().__init__(frame_width, frame_height)

        # Lumos-specific state
        self.lumos_state = 'idle'  # idle, flash, glow_in, active, fade_out
        self.lumos_start_time = None
        self.lumos_flicker_time = None
        self.lumos_flicker_intensity = 1.0
        self.lumos_prev_wand_pos: Optional[Tuple[float, float]] = None
        self.lumos_motion_speed = 0.0
        self._lumos_smooth_pos: Optional[Tuple[int, int]] = None

        # 🚀 PERFORMANCE OPTIMIZATION: Frame counter for reduced frequency effects
        self._frame_counter = 0

        # Random number generator for effects (seeded with system time for variety)
        self.rng = np.random.default_rng(int(time.time() * 1000000))

    def setup_scene(self):
        """Setup scene for Lumos."""
        self.lumos_state = 'idle'
        self.lumos_start_time = None
        self.lumos_flicker_time = None
        self.lumos_flicker_intensity = 1.0
        self.lumos_prev_wand_pos = None
        self.lumos_motion_speed = 0.0
        self._lumos_smooth_pos = None

    def activate(self, finger_pos: Optional[Tuple[float, float]] = None):
        """Activate Lumos spell."""
        if self.lumos_state == 'idle':
            self.lumos_state = 'flash'
            self.lumos_start_time = time.time()
            self.lumos_flicker_intensity = 1.0

    def deactivate(self):
        """Deactivate Lumos spell with smooth fade out."""
        if self.lumos_state in ['active', 'glow_in', 'flash']:
            # Transition to fade_out state for smooth deactivation from any active state
            self.lumos_state = 'fade_out'
            self.lumos_start_time = time.time()
        else:
            # If already idle or in fade_out, go directly to idle
            self._reset_lumos_state()

    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        """Update Lumos animation and position tracking."""
        # Always update position smoothing, even during fade_out
        self._update_position_smoothing(finger_pos)

        if self.lumos_state == 'idle':
            return

        # Handle animation state transitions and flickering behavior
        self._update_animation_state()
        self._update_flicker_behavior()
        self._update_motion_speed(finger_pos)

    def _update_position_smoothing(self, finger_pos: Optional[Tuple[float, float]]):
        """Update smooth position following for magical float effect."""
        if not finger_pos:
            return

        # Initialize smooth position if needed
        if not self._lumos_smooth_pos:
            self._lumos_smooth_pos = (
                int(finger_pos[0] * self.frame_width),
                int(finger_pos[1] * self.frame_height)
            )

        # Smooth position interpolation
        sx, sy = self._lumos_smooth_pos
        tx, ty = int(finger_pos[0] * self.frame_width), int(finger_pos[1] * self.frame_height)

        self._lumos_smooth_pos = (
            int(sx + (tx - sx) * self.POSITION_SMOOTHING_FACTOR),
            int(sy + (ty - sy) * self.POSITION_SMOOTHING_FACTOR)
        )

    def _update_animation_state(self):
        """Handle Lumos animation state transitions."""
        if self.lumos_start_time is None:
            return

        elapsed = time.time() - self.lumos_start_time

        # Animation timeline state transitions (cumulative timing)
        if self.lumos_state == 'flash' and elapsed >= self.FLASH_DURATION:
            self.lumos_state = 'glow_in'
        elif self.lumos_state == 'glow_in' and elapsed >= (self.FLASH_DURATION + self.GLOW_IN_DURATION):
            self.lumos_state = 'active'
            self.lumos_flicker_time = time.time()
        elif self.lumos_state == 'fade_out' and elapsed >= self.FADE_OUT_DURATION:
            # Fade out complete, reset to idle state
            self._reset_lumos_state()

    def _update_flicker_behavior(self):
        """Handle flickering behavior in active state."""
        if self.lumos_state != 'active' or self.lumos_flicker_time is None:
            return

        flicker_elapsed = time.time() - self.lumos_flicker_time
        flicker_interval = self.FLICKER_INTERVAL_MIN + (self.rng.random() * (self.FLICKER_INTERVAL_MAX - self.FLICKER_INTERVAL_MIN))

        if flicker_elapsed >= flicker_interval:
            # Generate new flicker intensity with controlled variation
            base_intensity = 1.0
            variation = (self.rng.random() - 0.5) * self.FLICKER_VARIATION_RANGE
            self.lumos_flicker_intensity = base_intensity + variation
            self.lumos_flicker_intensity = np.clip(
                self.lumos_flicker_intensity,
                self.FLICKER_INTENSITY_MIN,
                self.FLICKER_INTENSITY_MAX
            )

            # Reset flicker timer
            self.lumos_flicker_time = time.time()

    def _update_motion_speed(self, finger_pos: Optional[Tuple[float, float]]):
        """Calculate motion speed for dynamic radius expansion."""
        if not finger_pos:
            return

        if not self.lumos_prev_wand_pos:
            self.lumos_prev_wand_pos = finger_pos
            return

        # Calculate distance moved since last frame
        dx = finger_pos[0] - self.lumos_prev_wand_pos[0]
        dy = finger_pos[1] - self.lumos_prev_wand_pos[1]
        distance = math.hypot(dx, dy)  # More numerically stable than sqrt(dx*dx + dy*dy)

        # Smooth the motion speed for stable expansion
        self.lumos_motion_speed = (
            self.lumos_motion_speed * self.MOTION_SPEED_SMOOTHING +
            distance * (1.0 - self.MOTION_SPEED_SMOOTHING)
        )

        # Update previous position AFTER calculation (critical fix!)
        self.lumos_prev_wand_pos = finger_pos

    def _reset_lumos_state(self):
        """Reset Lumos to idle state."""
        self.lumos_state = 'idle'
        self.lumos_start_time = None
        self.lumos_flicker_time = None
        self.lumos_flicker_intensity = 1.0

    def draw(self, frame: np.ndarray, finger_pos: Optional[Tuple[float, float]] = None) -> np.ndarray:
        if self.lumos_state == 'idle':
            return frame

        if not self._lumos_smooth_pos and finger_pos:
            self._lumos_smooth_pos = (
                int(finger_pos[0] * self.frame_width),
                int(finger_pos[1] * self.frame_height)
            )

        if not self._lumos_smooth_pos:
            return frame

        cx, cy = self._lumos_smooth_pos

        # ==============================
        # Radius & animation parameters
        # ==============================
        base_radius = int(min(self.frame_width, self.frame_height) * self.BASE_RADIUS_RATIO)
        motion_expand = int(self.lumos_motion_speed * self.MOTION_EXPANSION_MULTIPLIER)
        max_radius = int(min(self.frame_width, self.frame_height) * self.MAX_RADIUS_RATIO)
        outer_radius = int(min(base_radius + motion_expand, max_radius))
        inner_radius = int(outer_radius * self.INNER_RADIUS_RATIO)
        mid_radius = int(outer_radius * self.MID_RADIUS_RATIO)

        # ==============================
        # ROI CLIP (🔥 MOST IMPORTANT)
        # ==============================
        r = outer_radius
        x1 = max(cx - r, 0)
        y1 = max(cy - r, 0)
        x2 = min(cx + r, self.frame_width)
        y2 = min(cy + r, self.frame_height)

        roi_w = x2 - x1
        roi_h = y2 - y1

        if roi_w <= 0 or roi_h <= 0:
            return frame

        roi = frame[y1:y2, x1:x2]

        # ==============================
        # Distance field (ROI ONLY)
        # ==============================
        yy, xx = np.ogrid[:roi_h, :roi_w]
        dx = xx - (cx - x1)
        dy = yy - (cy - y1)
        dist2 = dx * dx + dy * dy

        # ==============================
        # Gradients (NO sqrt, protected against division by zero, optimized)
        # ==============================
        # Add small epsilon to prevent division by zero when radius is 0
        epsilon = 1e-6
        inner_radius_sq = max(inner_radius ** 2, epsilon)
        mid_radius_sq = max(mid_radius ** 2, epsilon)
        outer_radius_sq = max(outer_radius ** 2, epsilon)

        # Optimized gradient calculations (faster than np.clip + power)
        inner = 1.0 - dist2 / inner_radius_sq
        inner[inner < 0] = 0
        inner *= inner  # **2

        mid = 1.0 - dist2 / mid_radius_sq
        mid[mid < 0] = 0
        mid **= 1.3

        outer = 1.0 - dist2 / outer_radius_sq
        outer[outer < 0] = 0
        outer **= 0.9

        # ==============================
        # Opacity by state
        # ==============================
        if self.lumos_state == 'glow_in':
            opacity = 0.6
        elif self.lumos_state == 'active':
            opacity = np.clip(0.65 * self.lumos_flicker_intensity, 0.5, 0.8)
        else:
            opacity = 0.5

        # ==============================
        # GOLDEN COLOR LAYERS (BGR)
        # ==============================
        inner_col = np.array([240, 250, 255], dtype=np.float32)
        mid_col   = np.array([120, 200, 255], dtype=np.float32)
        outer_col = np.array([40, 120, 200], dtype=np.float32)

        color = (
            inner[..., None] * inner_col * 1.0 +
            mid[..., None]   * mid_col   * 0.8 +
            outer[..., None] * outer_col * 0.4
        )

        color = np.clip(color, 0, 255).astype(np.uint8)

        # ==============================
        # Alpha mask (CIRCULAR, NO SQUARE)
        # ==============================
        alpha = (outer * opacity * 255).astype(np.uint8)
        overlay = cv2.merge([color[:, :, 0], color[:, :, 1], color[:, :, 2], alpha])

        # ==============================
        # Alpha blend (ROI only)
        # ==============================
        self._alpha_blend_roi(roi, overlay, 1.0)

        # ==============================
        # ADDITIVE LIGHT (🔥 MAGIC FEEL)
        # ==============================
        light = np.zeros_like(roi, dtype=np.float32)
        energy = outer * opacity
        light[:, :, 0] = energy * 60     # B
        light[:, :, 1] = energy * 160    # G
        light[:, :, 2] = energy * 255    # R

        self._additive_light_roi(roi, light, intensity=1.0)

        return frame


    def _alpha_blend_roi(self, roi_frame, overlay_bgra, alpha_multiplier=1.0):
        """
        Perform alpha blending with circular mask for true circular aura silhouette.
        No rectangular boundaries - alpha approaches zero smoothly at outer radius.
        """
        # Split overlay into RGB and alpha channels
        overlay_rgb = overlay_bgra[:, :, :3]
        overlay_alpha = overlay_bgra[:, :, 3].astype(np.float32) / 255.0 * alpha_multiplier

        # Expand alpha to 3 channels for element-wise multiplication
        alpha_3ch = np.stack([overlay_alpha] * 3, axis=2)

        # Perform alpha blending: result = overlay_rgb * alpha + roi_frame * (1 - alpha)
        blended = overlay_rgb.astype(np.float32) * alpha_3ch + roi_frame.astype(np.float32) * (1.0 - alpha_3ch)

        # Convert back to uint8
        roi_frame[:] = np.clip(blended, 0, 255).astype(np.uint8)

    def _additive_light_roi(self, roi_frame, light_rgb, intensity=1.0):
        """
        True light emission using additive blending.
        """
        roi_float = roi_frame.astype(np.float32)
        light_float = light_rgb.astype(np.float32) * intensity

        roi_float += light_float
        roi_frame[:] = np.clip(roi_float, 0, 255).astype(np.uint8)
