"""
Expecto Patronum Spell v3 (FIXED)
- Spiral guide following (screen-space correct)
- Alpha-based guide extraction
- Reliable progress tracking
- Debug overlay (progress, distance, state)
"""
import cv2
import time
import os
from typing import Optional, Tuple, List
import numpy as np
from .base import BaseSpell


class ExpectoPatronumSpell(BaseSpell):
    # ===== Tunable parameters =====
    MOVE_EPS = 4
    STOP_SPEED = 30.0
    PROGRESS_THRESHOLD = 0.65
    GUIDE_TOLERANCE_PX = 35      # how far finger can be from guide
    SMOKE_ALPHA = 0.4
    MAX_PATH_POINTS = 300
    START_TOLERANCE_PX = 40   # how close finger must be to start point

    def __init__(self, frame_width: int, frame_height: int, guide_path_png: str):
        super().__init__(frame_width, frame_height)

        self.active = False
        self.user_path: List[Tuple[int, int]] = []
        self.last_pos = None
        self.speed = 0.0
        self.patronus_locked = False
        self.started = False

        self.identification_pending = False
        self.identified_object = None

        self.image = None
        self.model_position = None
        self.animation_time = 0.0
        self.max_guide_idx = 0


        # ---- Load guide ----
        self.guide_img = cv2.imread(guide_path_png, cv2.IMREAD_UNCHANGED)
        if self.guide_img is None:
            raise RuntimeError(f"Failed to load guide image: {guide_path_png}")

        self.guide_points = self._extract_guide_points(self.guide_img)
        self.progress = 0.0
        self.last_guide_distance = 999.0

        # guide transform (image → screen)
        self._guide_transform = None

        self.smoke_layer = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        self._patronus_displayed = False

    # ======================================================
    # Properties (for spell engine compatibility)
    # ======================================================

    @property
    def path(self):
        """Alias for spell engine compatibility."""
        return self.user_path

    # ======================================================
    # Lifecycle
    # ======================================================

    def setup_scene(self):
        self._reset()

    def activate(self, finger_pos=None):
        self._reset()
        self.active = True

    def deactivate(self):
        self.active = False

    def _reset(self):
        self.user_path.clear()
        self.last_pos = None
        self.speed = 0.0
        self.progress = 0.0
        self.last_guide_distance = 999.0
        self.identification_pending = False
        self.identified_object = None
        self.image = None
        self.model_position = None
        self._patronus_displayed = False
        self.patronus_locked = False
        self.started = False
        self.max_guide_idx = 0


    # ======================================================
    # Update
    # ======================================================

    def update(self, dt: float, finger_pos: Optional[Tuple[float, float]] = None):
        if not self.active:
            return

        # If patronus is locked (final state), stop all drawing processing
        if self.patronus_locked:
            return

        finger_pixel = self._finger_to_pixel(finger_pos)
        if finger_pixel is None:
            return

        self._update_path(finger_pixel, dt)
        self._check_progress_and_stop()

        if self.identification_pending:
            self.animation_time += dt
            if self.animation_time >= 1.0:
                self.identification_pending = False
                self.patronus_locked = True

    def _finger_to_pixel(self, finger_pos):
        if finger_pos is None:
            return None
        if finger_pos[0] <= 1.0 and finger_pos[1] <= 1.0:
            return (
                int(finger_pos[0] * self.frame_width),
                int(finger_pos[1] * self.frame_height),
            )
        return int(finger_pos[0]), int(finger_pos[1])

    # ======================================================
    # Path + Progress
    # ======================================================

    def _update_path(self, point, dt):
        if self.last_pos is None:
            self.last_pos = point
            self.user_path.append(point)
            return

        dist = np.hypot(point[0] - self.last_pos[0], point[1] - self.last_pos[1])
        self.speed = dist / max(dt, 1e-6)

        if dist >= self.MOVE_EPS:
            self.user_path.append(point)
            if len(self.user_path) > self.MAX_PATH_POINTS:
                self.user_path.pop(0)
            self.last_pos = point

        self.progress = self._compute_progress(point)

    def _compute_progress(self, point):
        if not self.guide_points or self._guide_transform is None:
            return self.progress

        t = self._guide_transform
        guide = np.array(self.guide_points, dtype=np.float32)
        guide[:, 0] = guide[:, 0] * t["scale"] + t["x"]
        guide[:, 1] = guide[:, 1] * t["scale"] + t["y"]

        point = np.array(point, dtype=np.float32)

        # --------------------------------------------------
        # 1. START LOCK (must begin near first guide point)
        # --------------------------------------------------
        start_dist = np.linalg.norm(guide[0] - point)

        if not self.started:
            if start_dist <= self.START_TOLERANCE_PX:
                self.started = True
                self.max_guide_idx = 0
            else:
                self.last_guide_distance = start_dist
                return 0.0

        # --------------------------------------------------
        # 2. NORMAL PROGRESS TRACKING
        # --------------------------------------------------
        dists = np.linalg.norm(guide - point, axis=1)
        idx = int(np.argmin(dists))
        self.last_guide_distance = dists[idx]

        if self.last_guide_distance > self.GUIDE_TOLERANCE_PX:
            return self.progress

        # Allow small backward jitter (5%)
        backward_limit = int(len(guide) * 0.05)

        if idx >= self.max_guide_idx - backward_limit:
            self.max_guide_idx = max(self.max_guide_idx, idx)

        return self.max_guide_idx / max(len(guide) - 1, 1)

    def _check_progress_and_stop(self):
        if self.patronus_locked:
            return

        if (
            not self.identification_pending
            and self.progress >= self.PROGRESS_THRESHOLD
            and len(self.user_path) > 5
            and self.speed < self.STOP_SPEED
        ):
            self.identification_pending = True
            # Center the Patronus on screen instead of at drawing endpoint
            self.model_position = (self.frame_width // 2, self.frame_height // 2)
            self.animation_time = 0.0
            self.load_model("patronus")

    # ======================================================
    # Draw
    # ======================================================

    def draw(self, frame, finger_pos=None):
        if not self.active:
            return frame

        # Only show guide and path during drawing phase (before patronus is locked)
        if not self.patronus_locked:
            self._draw_guide(frame)
            self._draw_path(frame)
            self._draw_debug(frame)

        # Show patronus when it's active or locked
        if (self.identification_pending or self.patronus_locked) and self.image is not None:
            self._draw_smoke(frame)
            self._draw_patronus(frame)

        return frame


    def _draw_guide(self, frame):
        h, w = frame.shape[:2]
        gh, gw = self.guide_img.shape[:2]

        target_w = int(w * 0.25)
        scale = target_w / gw
        new_w = target_w
        new_h = int(gh * scale)

        guide_rgb = self.guide_img[:, :, :3]
        guide_resized = cv2.resize(guide_rgb, (new_w, new_h))

        x = (w - new_w) // 2
        y = (h - new_h) // 2

        self._guide_transform = {"x": x, "y": y, "scale": scale}

        roi = frame[y:y + new_h, x:x + new_w]
        frame[y:y + new_h, x:x + new_w] = cv2.addWeighted(
            roi, 1.0, guide_resized, 0.8, 0
        )

    def _draw_path(self, frame):
        if len(self.user_path) >= 2:
            pts = np.array(self.user_path, np.int32)
            cv2.polylines(frame, [pts], False, (200, 240, 255), 4, cv2.LINE_AA)

    def _draw_smoke(self, frame):
        x, y = self.model_position
        t = min(self.animation_time, 1.2)

        rng = np.random.default_rng(42)
        overlay = np.zeros_like(frame, dtype=np.uint8)

        num_puffs = int(8 + 12 * t)
        max_r = int(40 + 80 * t)

        for _ in range(num_puffs):
            angle = rng.uniform(0, 2 * np.pi)
            radius = rng.uniform(0, max_r)
            px = int(x + np.cos(angle) * radius)
            py = int(y + np.sin(angle) * radius)

            r = int(rng.uniform(20, 60) * (0.5 + t))
            cv2.circle(overlay, (px, py), r, (255, 255, 255), -1)

        alpha = max(0.0, 0.35 - 0.2 * t)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def _draw_patronus(self, frame):
        if self.image is None:
            return

        t = min(self.animation_time, 1.0)  # 0 → 1 sec
        ease = t * t * (3 - 2 * t)          # smoothstep

        scale = 0.3 + 0.7 * ease
        alpha = ease

        float_y = int(30 * (1 - ease))      # gentle upward float

        h0, w0 = self.image.shape[:2]
        w = int(w0 * scale)
        h = int(h0 * scale)

        img = cv2.resize(self.image, (w, h), interpolation=cv2.INTER_AREA)

        x, y = self.model_position
        x -= w // 2
        y -= h // 2 + float_y

        self._overlay_image_alpha(frame, img, x, y, alpha)


    def _draw_debug(self, frame):
        lines = [
            f"Progress: {self.progress:.2f} / {self.PROGRESS_THRESHOLD}",
            f"Guide dist: {self.last_guide_distance:.1f}px",
            f"Points: {len(self.user_path)}",
            f"State: {'CASTING' if self.identification_pending else 'DRAWING'}",
        ]
        y = 25
        for line in lines:
            cv2.putText(frame, line, (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 255), 2, cv2.LINE_AA)
            y += 22

    # ======================================================
    # Assets
    # ======================================================

    def load_model(self, name):
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join(os.getcwd(), "assets", "images", name + ext)
            if os.path.exists(path):
                self.image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                self.identified_object = name
                return True
        return False

    # ======================================================
    # Utils
    # ======================================================

    def _extract_guide_points(self, img, num_points=600):
        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        else:
            gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return []

        largest = max(contours, key=len)
        pts = np.array([p[0] for p in largest], dtype=np.float32)

        d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        s = np.concatenate(([0], np.cumsum(d)))
        total = s[-1]

        samples = np.linspace(0, total, num_points)
        out = []
        for v in samples:
            idx = np.searchsorted(s, v)
            idx = min(idx, len(pts) - 1)
            out.append(tuple(pts[idx].astype(int)))
        return out

    def _overlay_image(self, bg, fg, x, y):
        h, w = fg.shape[:2]
        H, W = bg.shape[:2]
        if x >= W or y >= H or x + w <= 0 or y + h <= 0:
            return

        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(W, x + w), min(H, y + h)

        fx1, fy1 = x1 - x, y1 - y
        fx2, fy2 = fx1 + (x2 - x1), fy1 + (y2 - y1)

        fg_crop = fg[fy1:fy2, fx1:fx2]
        bg_crop = bg[y1:y2, x1:x2]

        if fg_crop.shape[2] == 4:
            a = fg_crop[:, :, 3] / 255.0
            for c in range(3):
                bg_crop[:, :, c] = a * fg_crop[:, :, c] + (1 - a) * bg_crop[:, :, c]


    def _overlay_image_alpha(self, bg, fg, x, y, alpha_mul=1.0):
        h, w = fg.shape[:2]
        H, W = bg.shape[:2]

        if x >= W or y >= H or x + w <= 0 or y + h <= 0:
            return

        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(W, x + w), min(H, y + h)

        fx1, fy1 = x1 - x, y1 - y
        fx2, fy2 = fx1 + (x2 - x1), fy1 + (y2 - y1)

        fg_crop = fg[fy1:fy2, fx1:fx2]
        bg_crop = bg[y1:y2, x1:x2].astype(np.float32)

        if fg_crop.shape[2] != 4:
            return

        rgb = fg_crop[:, :, :3].astype(np.float32)
        alpha = (fg_crop[:, :, 3].astype(np.float32) / 255.0) * alpha_mul
        alpha_3 = alpha[:, :, None]

        # ----- NORMAL ALPHA BLEND -----
        out = rgb * alpha_3 + bg_crop * (1 - alpha_3)

        # ----- ADDITIVE GLOW -----
        glow_strength = 0.6
        glow = rgb * (1 - alpha_3) * glow_strength
        out += glow

        # ----- WRITE BACK (CRITICAL FIX) -----
        bg[y1:y2, x1:x2] = np.clip(out, 0, 255).astype(np.uint8)
