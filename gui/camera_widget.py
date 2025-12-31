"""
Camera widget for displaying live video feed with AR overlays.
"""
import cv2
import numpy as np
import os
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from typing import Optional
from core.hand_tracking import HandTracker
from core.spell_engine import SpellEngine, SpellType
from core.object_identifier import ObjectIdentifier
from gui.wizard_hat_overlay import WizardHatOverlay
from gui.wand_tracker import WandTracker


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
        self.spell_engine = spell_engine
        self.object_identifier = object_identifier
        self.running = False
        self.cap = None
        
        # Wand tracking
        self.wand_tracker = WandTracker(hand_tracker, smoothing_factor=0.5)
        
        # Identification state
        self.identification_thread: Optional[IdentificationThread] = None
        self.identification_requested = False

        # Wizard hat overlay
        self.wizard_hat_overlay = WizardHatOverlay()

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
            
            # Process hand tracking and get wand position
            wand_tip_normalized = self.wand_tracker.process_frame(frame, w, h)
            
            # Get hand bbox for face/hand discrimination
            hand_bbox = self.wand_tracker.get_hand_bbox(w, h)
            hand_bboxes = [hand_bbox] if hand_bbox else []
            
            # Update spell engine with wand position
            self.spell_engine.update(dt, wand_tip_normalized)

            # Reset identification_requested if spell changed or identification_pending is False
            if not hasattr(self, '_last_spell'):
                self._last_spell = None
            if (self._last_spell != self.spell_engine.current_spell or
                (self.spell_engine.current_spell == SpellType.EXPECTO_PATRONUM and not self.spell_engine.identification_pending)):
                self.identification_requested = False
            self._last_spell = self.spell_engine.current_spell

            # Add wizard hat overlay on face (throttled for performance)
            # Pass hand_bboxes to filter out false face detections
            frame = self.wizard_hat_overlay.process_frame(frame, hand_bboxes=hand_bboxes)

            # Draw spell effects
            # Use wand tip position directly
            frame = self.spell_engine.draw_effects(frame, wand_tip_normalized)
            
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

