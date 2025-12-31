"""
Camera widget for displaying live video feed with AR overlays.
"""
import cv2
import numpy as np
import os
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from core.hand_tracking import HandTracker
from core.spell_engine import SpellEngine, SpellType
from gui.wizard_hat_overlay import WizardHatOverlay
from gui.wand_tracker import WandTracker


class CameraThread(QThread):
    """Thread for capturing and processing video frames."""
    
    frame_ready = pyqtSignal(np.ndarray)
    # Removed spell_identified signal - no longer used
    
    def __init__(self, hand_tracker: HandTracker, spell_engine: SpellEngine):
        super().__init__()
        self.hand_tracker = hand_tracker
        self.spell_engine = spell_engine
        self.running = False
        self.cap = None
        
        # Wand tracking
        self.wand_tracker = WandTracker(hand_tracker, smoothing_factor=0.5)
        
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
            
            # Get hand bounding box for face detection filtering
            hand_bbox = self.wand_tracker.get_hand_bbox(w, h)
            hand_bboxes = [hand_bbox] if hand_bbox else []
            
            # Update spell engine with wand position
            self.spell_engine.update(dt, wand_tip_normalized)
            
            # Add wizard hat overlay on face (throttled for performance)
            frame = self.wizard_hat_overlay.process_frame(frame, hand_bboxes)

            # Draw spell effects
            frame = self.spell_engine.draw_effects(frame, wand_tip_normalized)
            
            # EXPECTO_PATRONUM now uses automatic patronus loading - no identification needed

            # Emit processed frame
            self.frame_ready.emit(frame)

    def stop(self):
        """Stop video capture."""
        self.running = False
        if self.cap:
            self.cap.release()
        self.wait()


class CameraWidget(QLabel):
    """Widget for displaying camera feed with AR overlays."""

    # Removed spell_identified signal - no longer used
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Camera not started")
        
        self.hand_tracker = HandTracker()
        self.spell_engine = SpellEngine(640, 480)
        self.camera_thread = None
        
        
    def start_camera(self, camera_index: int = 0):
        """Start camera capture."""
        if self.camera_thread and self.camera_thread.isRunning():
            self.stop_camera()
        
        self.camera_thread = CameraThread(self.hand_tracker, self.spell_engine)
        self.camera_thread.frame_ready.connect(self.update_frame)
        # Removed spell_identified connection - no longer used
        
        try:
            self.camera_thread.start_capture(camera_index)
        except Exception as e:
            self.setText(f"Camera error: {str(e)}")
            raise
    
    def stop_camera(self):
        """Stop camera capture."""
        if self.camera_thread:
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

