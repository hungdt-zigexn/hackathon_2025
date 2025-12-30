"""
Hand tracking module using MediaPipe for wand detection.
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, List
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:
    """Tracks hand landmarks and calculates wand position."""

    def __init__(self):
        import os
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'hand_landmarker.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hands = vision.HandLandmarker.create_from_options(options)
        self.hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
        self.frame_counter = 0
    
    def process_frame(self, frame: np.ndarray) -> Optional[List]:
        """
        Process a frame and return hand landmarks.

        Args:
            frame: BGR image frame from OpenCV

        Returns:
            List of landmark coordinates if hand detected, None otherwise
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        self.frame_counter += 1
        timestamp_ms = int(self.frame_counter * 33)  # Assuming ~30 fps

        results = self.hands.detect_for_video(mp_image, timestamp_ms)

        if results.hand_landmarks and len(results.hand_landmarks) > 0:
            # Return the first hand's landmarks
            return results.hand_landmarks[0]
        return None
    
    def get_wand_position(self, landmarks) -> Optional[Tuple[float, float]]:
        """
        Calculate wand tip position from hand landmarks.
        Wand is positioned at the tip of the index finger.

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            (x, y) tuple of wand tip position in normalized coordinates (0-1), or None
        """
        if landmarks is None:
            return None

        # Get index finger tip (landmark 8)
        # MediaPipe returns normalized coordinates (0-1)
        index_tip = landmarks[8]
        return (index_tip.x, index_tip.y)
    
    def get_wand_base(self, landmarks) -> Optional[Tuple[float, float]]:
        """
        Calculate wand base position (where wand starts from hand).
        Uses the middle finger MCP joint as the base.

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            (x, y) tuple of wand base position in normalized coordinates (0-1), or None
        """
        if landmarks is None:
            return None

        # Get middle finger MCP (landmark 9)
        # MediaPipe returns normalized coordinates (0-1)
        middle_mcp = landmarks[9]
        return (middle_mcp.x, middle_mcp.y)
    
    def draw_hand_landmarks(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """
        Draw hand landmarks on frame for debugging.

        Args:
            frame: BGR image frame
            landmarks: MediaPipe hand landmarks

        Returns:
            Frame with landmarks drawn
        """
        if landmarks:
            h, w = frame.shape[:2]
            # Draw connections
            for connection in self.hand_connections:
                start_idx, end_idx = connection
                start = landmarks[start_idx]
                end = landmarks[end_idx]
                start_point = (int(start.x * w), int(start.y * h))
                end_point = (int(end.x * w), int(end.y * h))
                cv2.line(frame, start_point, end_point, (0, 0, 255), 2)

            # Draw landmarks
            for landmark in landmarks:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        return frame
    
    def release(self):
        """Release resources."""
        self.hands.close()

