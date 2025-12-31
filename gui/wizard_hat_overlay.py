"""
Wizard hat overlay using face detection.
"""
import cv2
import numpy as np
import os
from typing import Optional, Tuple


class WizardHatOverlay:
    """Handles face detection and wizard hat overlay rendering."""
    
    def __init__(self):
        """Initialize face detection and load wizard hat image."""
        self.face_detection = self._init_face_detection()
        self.wizard_hat = self._load_wizard_hat()
        
        # Cache for hat rendering performance
        self._cached_hat_size = None
        self._cached_resized_hat = None
        self._cached_face_box = None
        self._cached_face_result = None
        
        # Face detection throttling for performance
        self._face_detection_counter = 0
        self._face_detection_interval = 5  # Detect every 5 frames (balanced: good FPS + responsive)
        
        # Performance optimization: downscale frame for detection
        self._detection_scale = 0.5  # Process at 50% resolution for faster detection (better FPS)
        self._cached_frame_size = None  # Cache original frame size
        
        # Smoothing for natural hat movement - simple exponential smoothing
        self._smoothed_face_box = None  # (x, y, w, h)
        self._smoothing_alpha = 0.5  # Balanced: smooth but responsive (0.5 = natural following)
        
        self._face_history = []  # List of (center_x, center_y) from recent frames
        self._max_history_size = 3  # Track last 3 detections (reduced for performance)
        self._stability_threshold = 0.25  # Max movement allowed (25% of frame size) - slightly relaxed
        self._min_stable_frames = 1  # Require at least 1 stable frame (reduced for faster response)
    
    def _init_face_detection(self):
        """Initialize MediaPipe face detection."""
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # Use short_range model with proper filtering
            model_path = os.path.join(os.getcwd(), "models", "blaze_face_short_range.tflite")
            if not os.path.exists(model_path):
                print(f"Warning: Face detection model not found at {model_path}")
                print(f"Please run: python3 download_face_model.py --model short_range")
                return None
            
            base_options = python.BaseOptions(
                model_asset_path=model_path,
                delegate=python.BaseOptions.Delegate.CPU
            )
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                min_detection_confidence=0.5,  # Balanced threshold - allow reasonable detections
                min_suppression_threshold=0.4  # Higher threshold to reduce false positives
            )
            face_detector = vision.FaceDetector.create_from_options(options)
            print(f"Face detection initialized: blaze_face_short_range.tflite")
            return face_detector
        except Exception as e:
            print(f"Warning: Could not initialize face detection: {e}")
            return None
    
    def _load_wizard_hat(self):
        """Load wizard hat image."""
        hat_path = os.path.join(os.getcwd(), "assets", "images", "cute_wizard_hat.png")
        hat_image = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
        if hat_image is None:
            print(f"Warning: Could not load wizard hat from {hat_path}")
            return None
        print(f"Loaded wizard hat: {hat_image.shape}")
        return hat_image
    
    def process_frame(self, frame: np.ndarray, hand_bboxes: list = None) -> np.ndarray:
        """
        Process wizard hat overlay with throttling.
        
        Args:
            frame: Input frame
            hand_bboxes: List of hand bounding boxes as (x, y, w, h) tuples for filtering
        """
        if self.wizard_hat is None or self.face_detection is None:
            return frame
        
        if hand_bboxes is None:
            hand_bboxes = []
        
        self._face_detection_counter += 1
        if self._face_detection_counter >= self._face_detection_interval:
            self._face_detection_counter = 0
            return self._overlay_wizard_hat(frame, hand_bboxes)
        elif self._cached_resized_hat is not None and self._cached_face_box is not None:
            # Use cached hat for better performance - render on every frame if cached
            return self._overlay_cached_hat(frame)
        return frame
    
    def _overlay_wizard_hat(self, frame: np.ndarray, hand_bboxes: list = None) -> np.ndarray:
        """
        Overlay wizard hat on detected faces.
        
        Args:
            frame: Input frame
            hand_bboxes: List of hand bounding boxes as (x, y, w, h) tuples for filtering
        """
        if hand_bboxes is None:
            hand_bboxes = []
            
        try:
            h, w, _ = frame.shape
            original_size = (w, h)
            
            # Cache frame size to track changes
            if self._cached_frame_size != original_size:
                self._cached_frame_size = original_size
            
            # Downscale frame for faster detection (performance optimization)
            detection_w = int(w * self._detection_scale)
            detection_h = int(h * self._detection_scale)
            
            # Resize frame for detection (use INTER_LINEAR for speed)
            detection_frame = cv2.resize(frame, (detection_w, detection_h), interpolation=cv2.INTER_LINEAR)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)

            # Create MediaPipe Image
            from mediapipe import Image, ImageFormat
            mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)

            # Detect faces on downscaled frame
            detection_result = self.face_detection.detect(mp_image)
            self._cached_face_result = detection_result  # Cache result

            if detection_result.detections:
                # Scale detection results back to original frame size
                scale_x = w / detection_w
                scale_y = h / detection_h
                
                # Scale detections to original frame size
                scaled_detections = self._scale_detections(detection_result.detections, scale_x, scale_y)
                
                valid_face = self._find_best_face(scaled_detections, w, h, hand_bboxes)
                
                if valid_face:
                    # Get current face box
                    bbox = valid_face.bounding_box
                    current_box = (bbox.origin_x, bbox.origin_y, bbox.width, bbox.height)
                    
                    # Apply simple exponential smoothing for natural movement
                    # This follows the head naturally without lag or jitter
                    if self._smoothed_face_box is not None:
                        # Simple exponential smoothing - natural and responsive
                        smoothed_box = tuple(int(c * self._smoothing_alpha + s * (1 - self._smoothing_alpha))
                                           for c, s in zip(current_box, self._smoothed_face_box))
                    else:
                        # First frame - use current position
                        smoothed_box = current_box
                    
                    self._smoothed_face_box = smoothed_box
                    
                    # Check if face box changed significantly (invalidate cache if needed)
                    if self._cached_face_box:
                        prev_w, prev_h = self._cached_face_box[2], self._cached_face_box[3]
                        if abs(prev_w - smoothed_box[2]) / max(prev_w, 1) > 0.1 or \
                           abs(prev_h - smoothed_box[3]) / max(prev_h, 1) > 0.1:
                            self._cached_resized_hat = None
                            self._cached_hat_size = None
                    
                    self._cached_face_box = smoothed_box
                    
                    # Create a simple object with smoothed coordinates for _place_hat_on_face
                    smoothed_face = type('obj', (object,), {
                        'bounding_box': type('obj', (object,), {
                            'origin_x': smoothed_box[0],
                            'origin_y': smoothed_box[1],
                            'width': smoothed_box[2],
                            'height': smoothed_box[3]
                        })()
                    })()
                    frame = self._place_hat_on_face(frame, smoothed_face)
                else:
                    # No valid face, clear cache and history
                    self._cached_resized_hat = None
                    self._cached_hat_size = None
                    self._cached_face_box = None
                    self._smoothed_face_box = None
                    self._face_history = []  # Clear history when no valid face
            else:
                # No detections, clear cache and history
                self._cached_resized_hat = None
                self._cached_hat_size = None
                self._cached_face_box = None
                self._smoothed_face_box = None
                self._face_history = []  # Clear history when no detections
        except Exception as e:
            print(f"Error in overlay_wizard_hat: {e}")

        return frame
    
    def _scale_detections(self, detections, scale_x: float, scale_y: float):
        """Scale detection bounding boxes from downscaled to original frame size."""
        scaled_detections = []
        for detection in detections:
            # Create a new detection object with scaled bounding box
            bbox = detection.bounding_box
            scaled_bbox = type('BoundingBox', (), {
                'origin_x': int(bbox.origin_x * scale_x),
                'origin_y': int(bbox.origin_y * scale_y),
                'width': int(bbox.width * scale_x),
                'height': int(bbox.height * scale_y)
            })()
            
            # Create scaled detection
            scaled_detection = type('Detection', (), {
                'bounding_box': scaled_bbox,
                'score': detection.score if hasattr(detection, 'score') else None
            })()
            scaled_detections.append(scaled_detection)
        
        return scaled_detections
    
    def _overlay_cached_hat(self, frame: np.ndarray) -> np.ndarray:
        """Overlay cached hat using smoothed position (already smooth from detection)."""
        if self._cached_resized_hat is None or self._cached_face_box is None:
            return frame
        
        try:
            # Use cached face box (already smoothed) - no interpolation needed
            # The smoothing is already applied during detection, so cached position is smooth
            bbox_x, bbox_y, bbox_w, bbox_h = self._cached_face_box
            h, w, _ = frame.shape
            
            # Get cached hat
            resized_hat = self._cached_resized_hat
            hat_width, hat_height = resized_hat.shape[1], resized_hat.shape[0]
            
            # Calculate hat position (same logic as _place_hat_on_face)
            hat_x = bbox_x - (hat_width - bbox_w) // 2
            head_top = bbox_y - int(bbox_h * 0.2)
            hat_y = head_top - int(hat_height * 0.9)
            
            if hat_y + hat_height < 0:
                hat_y = -int(hat_height * 0.3)
            elif hat_y < 0:
                pass
            else:
                hat_y = max(0, hat_y)
            
            return self._overlay_image_alpha(frame, resized_hat, hat_x, hat_y)
        except Exception as e:
            print(f"Error in overlay_cached_hat: {e}")
            return frame
    
    def _calculate_iou(self, bbox1: tuple, bbox2: tuple) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        Optimized with early exit for non-overlapping boxes.
        
        Args:
            bbox1: (x, y, w, h) in pixels
            bbox2: (x, y, w, h) in pixels
        
        Returns:
            IoU value (0-1)
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Early exit: check if boxes don't overlap at all (optimization)
        if x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1:
            return 0.0
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _is_center_in_bbox(self, center: tuple, bbox: tuple) -> bool:
        """
        Check if a point (center) is inside a bounding box.
        
        Args:
            center: (x, y) in pixels
            bbox: (x, y, w, h) in pixels
        
        Returns:
            True if center is inside bbox
        """
        cx, cy = center
        bx, by, bw, bh = bbox
        return bx <= cx <= bx + bw and by <= cy <= by + bh
    
    def _find_best_face(self, detections, frame_width: int, frame_height: int, hand_bboxes: list = None):
        """
        Filter detections to find the best face (not hand).
        
        Uses IoU gating and center-in-face check to reject face detections that overlap with hands.
        
        Args:
            detections: List of face detections
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            hand_bboxes: List of hand bounding boxes as (x, y, w, h) tuples
        """
        if hand_bboxes is None:
            hand_bboxes = []
            
        valid_face = None
        best_confidence = 0
        
        for detection in detections:
            bbox = detection.bounding_box
            x, y = bbox.origin_x, bbox.origin_y
            box_w, box_h = bbox.width, bbox.height
            
            # Get confidence
            confidence = 0.5
            if hasattr(detection, 'score') and detection.score:
                confidence = detection.score[0] if isinstance(detection.score, (list, tuple)) else detection.score
            
            # Calculate metrics
            min_size = min(frame_width, frame_height) * 0.08
            max_size = min(frame_width, frame_height) * 0.5
            aspect_ratio = box_w / box_h if box_h > 0 else 0
            center_x = x + box_w / 2
            center_y = y + box_h / 2
            
            if not (min_size <= box_w <= max_size and min_size <= box_h <= max_size):
                continue
            if not (0.7 <= aspect_ratio <= 1.3):
                continue
            if confidence < 0.5:
                continue
            if center_x < frame_width * 0.03 or center_x > frame_width * 0.97:
                continue
            
            face_bbox = (x, y, box_w, box_h)
            face_center = (center_x, center_y)
            
            if any(hand_bbox and (self._calculate_iou(face_bbox, hand_bbox) > 0.3 or 
                                  self._is_center_in_bbox(face_center, hand_bbox)) 
                   for hand_bbox in hand_bboxes):
                continue
            
            if self._cached_face_box is not None:
                cached_x, cached_y, cached_w, cached_h = self._cached_face_box
                cached_center_x = cached_x + cached_w / 2
                cached_center_y = cached_y + cached_h / 2
                
                # Calculate distance between centers
                distance = ((center_x - cached_center_x) ** 2 + (center_y - cached_center_y) ** 2) ** 0.5
                max_distance = min(frame_width, frame_height) * 0.3  # Allow 30% of frame size movement
                
                if distance > max_distance:
                    if confidence < 0.6:
                        continue
            
            # 7. Stability check - face should be stable across frames (hand moves fast)
            if len(self._face_history) > 0:
                # Calculate average position from history
                avg_x = sum(pos[0] for pos in self._face_history) / len(self._face_history)
                avg_y = sum(pos[1] for pos in self._face_history) / len(self._face_history)
                
                # Calculate distance from average
                distance = ((center_x - avg_x) ** 2 + (center_y - avg_y) ** 2) ** 0.5
                max_distance = min(frame_width, frame_height) * self._stability_threshold
                
                # Too far from recent average - likely hand (moves fast)
                # Require higher confidence or more history
                if distance > max_distance and (len(self._face_history) < self._min_stable_frames or confidence < 0.6):
                    continue
            
            if confidence > best_confidence:
                best_confidence = confidence
                valid_face = detection
                # Add to history for stability tracking
                self._face_history.append((center_x, center_y))
                if len(self._face_history) > self._max_history_size:
                    self._face_history.pop(0)
        
        # Clear history when no valid face found
        if not valid_face:
            self._face_history = []
        
        return valid_face
    
    def _get_resized_hat(self, box_w: int, box_h: int, frame_w: int, frame_h: int) -> Tuple[np.ndarray, int, int, int, int]:
        """Get resized hat image and position (cached for performance)."""
        # Calculate hat size
        face_ratio = max(box_w / frame_w, box_h / frame_h)
        if face_ratio > 0.3:
            hat_scale = 1.2 - (face_ratio - 0.3) * 1.5
            hat_scale = max(0.75, hat_scale)
        else:
            hat_scale = 1.2
        
        hat_width = int(box_w * hat_scale)
        hat_height = int(hat_width * self.wizard_hat.shape[0] / self.wizard_hat.shape[1])
        
        current_size = (hat_width, hat_height)
        if (self._cached_resized_hat is not None and 
            self._cached_hat_size == current_size):
            return self._cached_resized_hat, hat_width, hat_height, hat_scale, face_ratio
        
        # Resize and cache
        resized_hat = cv2.resize(self.wizard_hat, (hat_width, hat_height), interpolation=cv2.INTER_AREA)
        self._cached_resized_hat = resized_hat
        self._cached_hat_size = current_size
        
        return resized_hat, hat_width, hat_height, hat_scale, face_ratio
    
    def _place_hat_on_face(self, frame: np.ndarray, face_detection) -> np.ndarray:
        """Place wizard hat on detected face."""
        bbox = face_detection.bounding_box
        x, y = bbox.origin_x, bbox.origin_y
        box_w, box_h = bbox.width, bbox.height
        h, w, _ = frame.shape
        
        # Get resized hat (cached)
        resized_hat, hat_width, hat_height, _, _ = self._get_resized_hat(box_w, box_h, w, h)
        
        # Calculate hat position (on top of head)
        hat_x = x - (hat_width - box_w) // 2
        head_top = y - int(box_h * 0.2)  # Estimate head top (face box starts at forehead)
        hat_y = head_top - int(hat_height * 0.9)  # Place hat on head with slight overlap
        
        if hat_y + hat_height < 0:
            hat_y = -int(hat_height * 0.3)
        elif hat_y < 0:
            pass
        else:
            hat_y = max(0, hat_y)
        
        # Overlay (resized hat is cached)
        return self._overlay_image_alpha(frame, resized_hat, hat_x, hat_y)

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
