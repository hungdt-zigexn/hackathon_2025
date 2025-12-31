"""
Camera widget for displaying live video feed with AR overlays.
"""
import cv2
import numpy as np
import mediapipe as mp
import os
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from typing import Optional, Tuple
from core.hand_tracking import HandTracker
from core.spell_engine import SpellEngine, SpellType
from core.object_identifier import ObjectIdentifier


class IdentificationThread(QThread):
    """Background thread for pattern identification."""
    
    identification_complete = pyqtSignal(str)  # Emits object name when done
    
    def __init__(self, object_identifier: ObjectIdentifier, pattern_image: np.ndarray):
        super().__init__()
        self.object_identifier = object_identifier
        self.pattern_image = pattern_image.copy()  # Make a copy to avoid issues
    
    def run(self):
        """Run identification in background."""
        try:
            object_name = self.object_identifier.identify_from_canvas(self.pattern_image)
            self.identification_complete.emit(object_name)
        except Exception as e:
            print(f"Error in identification thread: {e}")
            self.identification_complete.emit("wand")  # Default fallback


class CameraThread(QThread):
    """Thread for capturing and processing video frames."""
    
    frame_ready = pyqtSignal(np.ndarray)
    spell_identified = pyqtSignal(str)
    
    def __init__(self, hand_tracker: HandTracker, spell_engine: SpellEngine, object_identifier: Optional[ObjectIdentifier] = None):
        super().__init__()
        self.hand_tracker = hand_tracker
        self.spell_engine = spell_engine
        self.object_identifier = object_identifier
        self.running = False
        self.cap = None
        # Smoothing state
        self.prev_wand_tip = None
        self.prev_wand_base = None
        self.smoothing_factor = 0.5  # Higher = more responsive, Lower = smoother
        # Identification state
        self.identification_thread: Optional[IdentificationThread] = None
        self.identification_requested = False

        # Face detection for wizard hat using new MediaPipe API
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # Download model if needed
            model_path = os.path.join(os.getcwd(), "models", "face_detector.tflite")
            if not os.path.exists(model_path):
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                import urllib.request
                model_url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
                print("Downloading face detection model...")
                urllib.request.urlretrieve(model_url, model_path)
                print("Model downloaded successfully")

            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                min_detection_confidence=0.5
            )
            self.face_detection = vision.FaceDetector.create_from_options(options)
        except Exception as e:
            print(f"Warning: Could not initialize face detection: {e}")
            self.face_detection = None
        # Load wizard hat image
        hat_path = os.path.join(os.getcwd(), "assets", "images", "cute_wizard_hat.png")
        self.wizard_hat = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
        if self.wizard_hat is None:
            print(f"Warning: Could not load wizard hat from {hat_path}")
        else:
            print(f"Loaded wizard hat: {self.wizard_hat.shape}")
        
    def start_capture(self, camera_index: int = 0):
        """Start video capture."""
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")
        self.running = True
        self.start()
    
    def run(self):
        """Main thread loop."""
        import time
        last_time = time.time()
        
        while self.running:
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Flip frame horizontally (mirror effect)
            frame = cv2.flip(frame, 1)
            
            # Update frame size in spell engine
            h, w = frame.shape[:2]
            self.spell_engine.update_frame_size(w, h)
            
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Process hand tracking
            landmarks = self.hand_tracker.process_frame(frame)
            
            # Get wand position
            wand_tip = None
            wand_base = None
            wand_tip_normalized = None
            
            if landmarks:
                # MediaPipe returns normalized coordinates (0-1)
                raw_tip_norm = self.hand_tracker.get_wand_position(landmarks)
                raw_base_norm = self.hand_tracker.get_wand_base(landmarks)
                
                # Apply smoothing to Tip
                if raw_tip_norm:
                    curr_tip_x = raw_tip_norm[0] * w
                    curr_tip_y = raw_tip_norm[1] * h
                    
                    if self.prev_wand_tip:
                        smooth_x = curr_tip_x * self.smoothing_factor + self.prev_wand_tip[0] * (1 - self.smoothing_factor)
                        smooth_y = curr_tip_y * self.smoothing_factor + self.prev_wand_tip[1] * (1 - self.smoothing_factor)
                        self.prev_wand_tip = (smooth_x, smooth_y)
                    else:
                        self.prev_wand_tip = (curr_tip_x, curr_tip_y)
                    
                    wand_tip = (int(self.prev_wand_tip[0]), int(self.prev_wand_tip[1]))
                    wand_tip_normalized = (self.prev_wand_tip[0] / w, self.prev_wand_tip[1] / h)
                
                # Apply smoothing to Base
                if raw_base_norm:
                    curr_base_x = raw_base_norm[0] * w
                    curr_base_y = raw_base_norm[1] * h
                    
                    if self.prev_wand_base:
                        smooth_x = curr_base_x * self.smoothing_factor + self.prev_wand_base[0] * (1 - self.smoothing_factor)
                        smooth_y = curr_base_y * self.smoothing_factor + self.prev_wand_base[1] * (1 - self.smoothing_factor)
                        self.prev_wand_base = (smooth_x, smooth_y)
                    else:
                        self.prev_wand_base = (curr_base_x, curr_base_y)
                    
                    wand_base = (int(self.prev_wand_base[0]), int(self.prev_wand_base[1]))
            else:
                # Reset smoothing if hand lost
                self.prev_wand_tip = None
                self.prev_wand_base = None
            self.spell_engine.update(dt, wand_tip_normalized)

            # Reset identification_requested if spell changed or identification_pending is False
            if not hasattr(self, '_last_spell'):
                self._last_spell = None
            if (self._last_spell != self.spell_engine.current_spell or
                (self.spell_engine.current_spell == SpellType.EXPECTO_PATRONUM and not self.spell_engine.identification_pending)):
                self.identification_requested = False
            self._last_spell = self.spell_engine.current_spell
            
            # Draw wand and get visual tip
            visual_tip = None
            if wand_tip:
                visual_tip = wand_tip

            # Add wizard hat overlay on face
            if self.wizard_hat is not None and self.face_detection is not None:
                frame = self._overlay_wizard_hat(frame)
            
            # Draw spell effects
            # Use finger tip position directly (wand drawing removed)
            final_effect_pos = wand_tip_normalized if landmarks else None
            
            frame = self.spell_engine.draw_effects(frame, final_effect_pos)
            
            # Check if EXPECTO_PATRONUM spell needs identification
            if (self.spell_engine.current_spell == SpellType.EXPECTO_PATRONUM and
                self.spell_engine.identification_pending and
                not self.identification_requested and
                self.object_identifier is not None):

                self.identification_requested = True
                # Extract pattern image from patronum_path
                if len(self.spell_engine.patronum_path) > 1:
                    # Create a canvas image with the drawn path
                    canvas = np.zeros((h, w, 3), dtype=np.uint8)
                    canvas.fill(255)  # White background

                    # Draw the path in black
                    pts = np.array(self.spell_engine.patronum_path, np.int32)
                    cv2.polylines(canvas, [pts], False, (0, 0, 0), 5, cv2.LINE_AA)

                    # Start identification in background thread
                    self.identification_thread = IdentificationThread(self.object_identifier, canvas)
                    self.identification_thread.identification_complete.connect(self.on_identification_complete)
                    self.identification_thread.start()

            # Emit processed frame
            self.frame_ready.emit(frame)

            # Small delay to prevent overwhelming the system
            self.msleep(33)  # ~30 FPS
    
    def on_identification_complete(self, object_name: str):
        """Handle identification completion."""
        print(f"[DEBUG] Identification complete: {object_name}")
        self.spell_engine.identification_pending = False
        self.spell_engine.identified_object = object_name
        
        # Load the Patronum model
        if self.spell_engine.load_patronum_model(object_name):
            print(f"[DEBUG] Model loaded successfully: {object_name}")
        else:
            print(f"[DEBUG] Failed to load model: {object_name}")
        
        # Emit signal
        self.spell_identified.emit(object_name)
        
        # Clean up thread
        if self.identification_thread:
            self.identification_thread.wait()
            self.identification_thread = None

    def _overlay_wizard_hat(self, frame: np.ndarray) -> np.ndarray:
        """Overlay wizard hat on detected faces."""
        try:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create MediaPipe Image
            from mediapipe import Image, ImageFormat
            mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)

            # Detect faces
            detection_result = self.face_detection.detect(mp_image)

            if detection_result.detections:
                h, w, _ = frame.shape
                valid_face = self._find_best_face(detection_result.detections, w, h)
                
                if valid_face:
                    frame = self._place_hat_on_face(frame, valid_face)
        except Exception as e:
            print(f"Error in overlay_wizard_hat: {e}")

        return frame
    
    def _find_best_face(self, detections, frame_width: int, frame_height: int):
        """Filter detections to find the best face (not hand)."""
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
            
            # Apply filters
            min_size, max_size = min(frame_width, frame_height) * 0.08, min(frame_width, frame_height) * 0.5
            aspect_ratio = box_w / box_h if box_h > 0 else 0
            center_x, center_y = x + box_w / 2, y + box_h / 2
            
            if not (min_size <= box_w <= max_size and min_size <= box_h <= max_size):
                continue  # Size filter
            if not (0.6 <= aspect_ratio <= 1.4):
                continue  # Aspect ratio filter
            if center_y > frame_height * 0.8:
                continue  # Position filter (upper 80%)
            if confidence < 0.5:
                continue  # Confidence filter
            if center_x < frame_width * 0.05 or center_x > frame_width * 0.95:
                continue  # Edge position filter
            
            # Keep best confidence
            if confidence > best_confidence:
                best_confidence = confidence
                valid_face = detection
        
        return valid_face
    
    def _place_hat_on_face(self, frame: np.ndarray, face_detection) -> np.ndarray:
        """Place wizard hat on detected face."""
        bbox = face_detection.bounding_box
        x, y = bbox.origin_x, bbox.origin_y
        box_w, box_h = bbox.width, bbox.height
        h, w, _ = frame.shape
        
        # Adaptive hat size: face large (near camera) → hat smaller
        # Calculate face ratio so với frame
        face_ratio = max(box_w / w, box_h / h)
        if face_ratio > 0.3:
            hat_scale = 1.2 - (face_ratio - 0.3) * 1.5
            hat_scale = max(0.75, hat_scale)
        else:
            hat_scale = 1.2
        
        # Calculate hat size
        hat_width = int(box_w * hat_scale)
        hat_height = int(hat_width * self.wizard_hat.shape[0] / self.wizard_hat.shape[1])
        
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
        
        # Resize and overlay
        resized_hat = cv2.resize(self.wizard_hat, (hat_width, hat_height), interpolation=cv2.INTER_AREA)
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

    def stop(self):
        """Stop video capture."""
        self.running = False
        if self.cap:
            self.cap.release()
        self.wait()


class CameraWidget(QLabel):
    """Widget for displaying camera feed with AR overlays."""
    
    spell_identified = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Camera not started")
        
        self.hand_tracker = HandTracker()
        self.spell_engine = SpellEngine(640, 480)
        self.camera_thread = None
        
        # Initialize ObjectIdentifier (lazy initialization on first use)
        self.object_identifier: Optional[ObjectIdentifier] = None
        
    def start_camera(self, camera_index: int = 0):
        """Start camera capture."""
        if self.camera_thread and self.camera_thread.isRunning():
            self.stop_camera()
        
        # Initialize ObjectIdentifier if not already done
        if self.object_identifier is None:
            try:
                import os
                api_key = os.getenv('GOOGLE_API_KEY')
                if api_key:
                    self.object_identifier = ObjectIdentifier(api_key=api_key)
                    print("[DEBUG] ObjectIdentifier initialized")
                else:
                    print("[WARNING] GOOGLE_API_KEY not set, pattern identification will not work")
            except Exception as e:
                print(f"[WARNING] Failed to initialize ObjectIdentifier: {e}")
        
        self.camera_thread = CameraThread(self.hand_tracker, self.spell_engine, self.object_identifier)
        self.camera_thread.frame_ready.connect(self.update_frame)
        self.camera_thread.spell_identified.connect(self.spell_identified.emit)
        
        try:
            self.camera_thread.start_capture(camera_index)
        except Exception as e:
            self.setText(f"Camera error: {str(e)}")
            raise
    
    def stop_camera(self):
        """Stop camera capture."""
        if self.camera_thread:
            # Wait for any identification thread to finish
            if self.camera_thread.identification_thread:
                self.camera_thread.identification_thread.wait()
            self.camera_thread.stop()
            self.camera_thread = None
    
    def update_frame(self, frame: np.ndarray):
        """Update displayed frame."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
    
    def get_spell_engine(self) -> SpellEngine:
        """Get the spell engine instance."""
        return self.spell_engine
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.stop_camera()
        self.hand_tracker.release()
        super().closeEvent(event)

