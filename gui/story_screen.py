import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from core.voice_verifier import VoiceVerifier
from core.story_manager import StoryManager, StoryStepType
from core.spell_engine import SpellType
from gui.camera_widget import CameraWidget
from gui.utils import SpellVerificationThread
from gui.theme import HOGWARTS_STYLE

class StoryScreen(QWidget):
    """Game screen handling the storyline and spell casting."""
    
    finished = pyqtSignal()  # Signal when game is completed or exited

    def __init__(self, parent=None):
        super().__init__(parent)
        self.story_manager = StoryManager()
        self.voice_verifier: VoiceVerifier = None
        self.verification_thread: SpellVerificationThread = None
        self.is_listening = False
        self.level_completed = False
        self.game_active = False
        self.auto_retry_timer = QTimer(self)
        self.auto_retry_timer.setSingleShot(True)
        self.auto_retry_timer.timeout.connect(self.start_listening)

        self.success_timer = QTimer(self)
        self.success_timer.setSingleShot(True)
        self.success_timer.timeout.connect(self.next_level)

        self.retry_count = 0

        # 🏰 Hogwarts Wizarding UI – Global Stylesheet
        self.setStyleSheet(HOGWARTS_STYLE)

        self.init_ui()
        
    def set_status_message(self, text, style="info"):
        # Apply status-specific styling using setProperty for dynamic theming
        self.status_label.setProperty("statusStyle", style)

        # Force stylesheet refresh
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.status_label.setText(f"✧ {text} ✧")

    def set_camera_spell_state(self, state=None):
        """Set the spell state for camera mirror glow effects.

        Args:
            state: "active" for active spell glow, "patronus" for patronus glow, None to clear
        """
        self.camera_widget.setProperty("spellState", state)

        # Force stylesheet refresh
        self.camera_widget.style().unpolish(self.camera_widget)
        self.camera_widget.style().polish(self.camera_widget)

    def set_cinematic_mode(self, enabled=False):
        """Enable/disable cinematic mode for Expecto Patronum.

        Args:
            enabled: True to enable cinematic mode, False to disable
        """
        if enabled:
            self.setObjectName("CinematicMode")
        else:
            self.setObjectName("")

        # Force stylesheet refresh
        self.style().unpolish(self)
        self.style().polish(self)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Balanced spacing between widgets
        layout.setContentsMargins(30, 30, 30, 20)  # Reduced bottom margin
        
        # 📜 TITLE – Ancient Chapter Header
        self.title_label = QLabel("")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 📖 STORY PANEL – Parchment Scroll
        self.story_text = QLabel("")
        self.story_text.setObjectName("StoryText")
        self.story_text.setFont(QFont("Arial", 14))
        self.story_text.setWordWrap(True)
        self.story_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.story_text)
        
        # 📦 CAMERA + HUD CONTAINER – Keep them together
        self.camera_hud_container = QWidget()
        camera_hud_layout = QVBoxLayout(self.camera_hud_container)
        camera_hud_layout.setSpacing(0)  # No spacing between camera and HUD
        camera_hud_layout.setContentsMargins(0, 0, 0, 0)

        # 🪞 CAMERA – Magic Mirror / Pensieve
        self.camera_widget = CameraWidget()
        self.camera_widget.setObjectName("CameraMirror")
        self.camera_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Removed spell_identified connection - patronus success now handled automatically
        camera_hud_layout.addWidget(self.camera_widget, stretch=1)  # Camera expands within container

        # 🪄 SPELL HUD – Status + Mana Control Zone
        self.spell_hud = QWidget()
        self.spell_hud.setObjectName("SpellHUD")

        hud_layout = QVBoxLayout(self.spell_hud)
        hud_layout.setSpacing(8)
        hud_layout.setContentsMargins(12, 10, 12, 5)

        # 🪄 STATUS BAR – Spell Aura
        self.status_label = QLabel("Hãy đọc phép thuật khi bạn sẵn sàng")
        self.status_label.setObjectName("StatusBar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(56)
        self.set_status_message("Hãy đọc phép thuật khi bạn sẵn sàng", "info")
        hud_layout.addWidget(self.status_label)

        # ⚡ MANA BAR – Magical Energy
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        hud_layout.addWidget(self.progress_bar)

        camera_hud_layout.addWidget(self.spell_hud, stretch=0)  # HUD stays at bottom

        # Add camera+HUD container to main layout
        layout.addWidget(self.camera_hud_container, stretch=1)  # Container takes remaining space
        
        # 🧙 BUTTONS – Wizard Controls (styles now handled globally)

        # Navigation and control buttons
        self.controls_layout = QHBoxLayout()

        # Navigation buttons
        self.back_btn = QPushButton("← Quay lại")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)
        self.controls_layout.addWidget(self.back_btn)

        # Action buttons (skip/retry/next)
        self.skip_btn = QPushButton("Bỏ qua")
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.clicked.connect(self.skip_current_step)
        self.skip_btn.setVisible(False)
        self.controls_layout.addWidget(self.skip_btn)

        self.retry_btn = QPushButton("Thử lại")
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.clicked.connect(self.retry_current_spell)
        self.retry_btn.setVisible(False)
        self.controls_layout.addWidget(self.retry_btn)

        self.next_spell_btn = QPushButton("Phép tiếp theo →")
        self.next_spell_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_spell_btn.clicked.connect(self.go_next_spell)
        self.next_spell_btn.setVisible(False)
        self.controls_layout.addWidget(self.next_spell_btn)
        
        layout.addLayout(self.controls_layout)
        
        self.setLayout(layout)
        
        # Keep focus for accessibility/keyboard shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def go_back(self):
        """Go back to the previous spell."""
        if self.story_manager.go_back():
            self.load_step()

    def go_next_spell(self):
        """Go to the next spell (after completion)."""
        step = self.story_manager.get_current_step()
        if step and not step.next_step_id:
            # Final spell - exit game
            self.exit_game()
        else:
            # Go to next spell
            self.next_level()

    def skip_current_step(self):
        """Skip the current step and advance to the next one."""
        if self.story_manager.skip_step():
            self.load_step()
        else:
            # No more steps, end game
            self.exit_game()

    def retry_current_spell(self):
        """Retry the current spell attempt."""
        # Reset completion state
        self.level_completed = False
        self.retry_btn.setVisible(False)
        self.next_spell_btn.setVisible(False)

        # Reset UI to show skip button and spell interface
        self.skip_btn.setVisible(True)

        # Restart the spell process
        step = self.story_manager.get_current_step()
        if step and step.step_type == StoryStepType.PRACTICE:
            self.start_listening()
        elif step and step.step_type == StoryStepType.EXPLANATION:
            # For explanation steps, just show the next button
            self.next_spell_btn.setText("Bắt đầu →")
            self.next_spell_btn.setVisible(True)

    def on_control_clicked(self):
        """Handle main control button click (Next/Start/Continue)."""
        if self.next_spell_btn.text() == "Kết thúc":
            self.exit_game()
            return

        step = self.story_manager.get_current_step()
        if not step:
            return

        if self.level_completed or step.step_type == StoryStepType.EXPLANATION:
            self.next_level()
        # Note: Retry functionality is now handled by the dedicated retry button

    def start_game(self):
        """Initialize game state."""
        self.story_manager.reset()
        self.level_completed = False
        self.is_listening = False
        self.game_active = False
        self.auto_retry_timer.stop()
        self.success_timer.stop()
        if self.verification_thread:
            try:
                self.verification_thread.finished.disconnect()
            except:
                pass
            if self.verification_thread.isRunning():
                self.verification_thread.wait(5000)
            self.verification_thread.deleteLater()
            self.verification_thread = None
        
        # Init voice verifier
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                QMessageBox.warning(self, "API Key Missing", "Please set GOOGLE_API_KEY environment variable.")
                return
            self.voice_verifier = VoiceVerifier(api_key=api_key)
            self.camera_widget.start_camera()
            self.game_active = True
            self.load_step()
            self.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể khởi động game: {str(e)}")

    def load_step(self):
        """Load current story step data."""
        step = self.story_manager.get_current_step()
        if not step:
            return

        self.title_label.setText(f"Chapter {step.id}: {step.title}")
        self.story_text.setText(step.description)
        self.level_completed = False
        self.is_listening = False
        self.retry_count = 0
        self.auto_retry_timer.stop()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.success_timer.stop()
        self.retry_btn.setVisible(False)  # Hide retry button when loading new step
        self.next_spell_btn.setVisible(False)  # Hide next spell button when loading new step

        # Show back button if not on first step
        self.back_btn.setVisible(step.id > 1)

        # Reset spell engine visuals between steps
        if self.camera_widget.spell_engine:
            self.camera_widget.spell_engine.deactivate_spell()
            
            # For practice steps, setup the scene (e.g., show Leviosa box)
            if step.step_type == StoryStepType.PRACTICE and step.required_spell:
                print(f"[DEBUG] Setting up scene for spell: {step.required_spell}")
                self.camera_widget.spell_engine.setup_spell_scene(step.required_spell)

        if step.step_type == StoryStepType.EXPLANATION:
            spell_name = step.required_spell.value if step.required_spell else "phép thuật"
            self.set_status_message(
                f"Giới thiệu phép: học '{spell_name}' rồi nhấn Bắt đầu.",
                "info"
            )
            self.next_spell_btn.setText("Bắt đầu →")
            self.next_spell_btn.setVisible(True)
            self.next_spell_btn.setEnabled(True)
            self.skip_btn.setVisible(True)
            self.skip_btn.setEnabled(True)
        else:
            spell_name = step.required_spell.value if step.required_spell else "phép thuật"
            self.set_status_message(f"Hãy nói '{spell_name}' khi bạn sẵn sàng.", "info")
            self.next_spell_btn.setVisible(False)
            self.skip_btn.setVisible(True)
            self.skip_btn.setEnabled(True)
            # Start automatic listening shortly after practice step loads
            self.schedule_spell_detection(delay_ms=1500)
    
    def schedule_spell_detection(self, delay_ms: int = 0):
        """Start or schedule automatic spell detection."""
        if (
            not self.voice_verifier
            or self.level_completed
            or not self.game_active
        ):
            return
        
        self.auto_retry_timer.stop()
        if delay_ms <= 0:
            self.start_listening()
        else:
            self.auto_retry_timer.start(delay_ms)
            
    def start_listening(self):
        if (
            not self.voice_verifier
            or self.is_listening
            or self.level_completed
            or not self.game_active
        ):
            return
        
        step = self.story_manager.get_current_step()
        if not step or step.step_type != StoryStepType.PRACTICE:
            return
        
        # Check for EXPECTO_PATRONUM spell to bypass verification
        if step.required_spell == SpellType.EXPECTO_PATRONUM:
            self.handle_patronum_sequence()
            return
        
        self.auto_retry_timer.stop()
        self.is_listening = True
        spell_name = step.required_spell.value
        self.set_status_message("🪄 Ma lực đang lắng nghe lời gọi của bạn... Hãy nói rõ ràng.", "listening")
        self.progress_bar.setRange(0, 0)

        is_retry = self.retry_count > 0
        self.verification_thread = SpellVerificationThread(self.voice_verifier, spell_name, is_retry=is_retry)
        self.verification_thread.recording_finished.connect(self.on_recording_finished)
        self.verification_thread.verification_complete.connect(self.on_verification_complete)
        self.verification_thread.start()

    def handle_patronum_sequence(self):
        """Handle the Expecto Patronum spell sequence (Wait -> Draw -> Identify)."""
        self.auto_retry_timer.stop()
        self.is_listening = True

        # 1. Wait for user to speak (simulated)
        self.set_status_message("Đang nghe 'Expecto Patronum'...", "listening")
        QTimer.singleShot(2000, self.start_patronum_drawing)

    def start_patronum_drawing(self):
        """Start the drawing phase."""
        if not self.game_active:
            return

        self.set_status_message("✨ Hãy vẽ ký hiệu theo luồng ánh sáng để triệu hồi Thần hộ mệnh ✨", "info")
        self.progress_bar.setRange(0, 100) # Show progress
        self.progress_bar.setValue(0)

        # Activate spell to start recording
        self.camera_widget.get_spell_engine().activate_spell(SpellType.EXPECTO_PATRONUM)

        # Start monitoring for Patronus appearance
        self._patronus_monitor_timer = QTimer(self)
        self._patronus_monitor_timer.timeout.connect(self._check_patronus_status)
        self._patronus_monitor_timer.start(100)  # Check every 100ms

    def _check_patronus_status(self):
        """Check if Patronus has appeared and handle completion."""
        if not self.game_active:
            self._patronus_monitor_timer.stop()
            return

        spell_engine = self.camera_widget.get_spell_engine()
        expecto_spell = spell_engine.expecto_patronum

        # Check if Patronus has appeared (locked state)
        if expecto_spell.patronus_locked and expecto_spell.image is not None:
            self._patronus_monitor_timer.stop()
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)

            # Handle the spell completion properly
            step = self.story_manager.get_current_step()
            if step and step.required_spell == SpellType.EXPECTO_PATRONUM:
                self.handle_practice_success("Patronus của bạn đã hiện hình!")
                print("[DEBUG] Patronus appeared - completion handled")

    # Removed on_patronum_identified - patronus success now handled automatically

    def on_recording_finished(self):
        """Called when audio recording is done, but verification is still in progress."""
        self.set_status_message("Đang giải mã phép thuật...", "validating")

    def on_verification_complete(self, is_correct: bool, feedback: str):
        self.is_listening = False
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        
        # Don't delete the thread here - it's still running speak_feedback()
        # Instead, connect to the finished signal for cleanup
        if self.verification_thread:
            self.verification_thread.finished.connect(self._cleanup_verification_thread)
        
        if not self.game_active:
            return
        
        if is_correct:
            self.handle_practice_success(feedback)
        else:
            print(f"[DEBUG] Verification failed! Showing retry button. Retry count: {self.retry_count}")
            self.retry_count += 1
            retry_feedback = feedback or "Chưa chính xác lắm."
            self.set_status_message(
                f"{retry_feedback}\nNhấn 'Thử lại' để thử lần nữa hoặc 'Bỏ qua' để bỏ qua phép này.",
                "error"
            )
            self.retry_btn.setVisible(True)
            self.retry_btn.setEnabled(True)
            self.skip_btn.setVisible(True)  # Keep skip button visible for retries
            self.retry_btn.setFocus()
            print(f"[DEBUG] Retry button should now be visible: {self.retry_btn.isVisible()}")
    
    def _cleanup_verification_thread(self):
        """Clean up the verification thread after it finishes."""
        if self.verification_thread:
            self.verification_thread.deleteLater()
            self.verification_thread = None

    def handle_practice_success(self, feedback: str):
        self.level_completed = True
        self.auto_retry_timer.stop()
        self.is_listening = False
        step = self.story_manager.get_current_step()
        if not step:
            return
        
        # Activate Visuals
        print(f"[DEBUG STORY] handle_practice_success called, activating spell: {step.required_spell}")
        # Avoid resetting EXPECTO_PATRONUM spell if it was just identified and is showing the model
        if step.required_spell != SpellType.EXPECTO_PATRONUM:
            self.camera_widget.get_spell_engine().activate_spell(step.required_spell, None)
        
        # Update UI
        success_text = f"Thành công! {step.success_message}"
        if feedback:
            success_text = f"{success_text}\n{feedback}"
        self.set_status_message(success_text, "success")

        # Show completion options - retry or continue to next spell
        if step.next_step_id:
            # Not the final spell - show retry and next options
            self.retry_btn.setVisible(True)
            self.retry_btn.setEnabled(True)
            self.next_spell_btn.setText("Phép tiếp theo →")
            self.next_spell_btn.setVisible(True)
            self.next_spell_btn.setEnabled(True)
            self.skip_btn.setVisible(False)  # Hide skip during completion
            self.retry_btn.setFocus()
        else:
            # Final spell completed - show completion and exit option
            self.set_status_message("Chúc mừng! Bạn đã hoàn thành khóa học phù thủy nghiệp dư!", "success")
            self.next_spell_btn.setText("Kết thúc")
            self.next_spell_btn.setVisible(True)
            self.next_spell_btn.setEnabled(True)
            self.next_spell_btn.setFocus()
            self.retry_btn.setVisible(False)
            self.skip_btn.setVisible(False)

    def next_level(self):
        self.auto_retry_timer.stop()
        self.success_timer.stop()
        if hasattr(self, '_patronus_monitor_timer'):
            self._patronus_monitor_timer.stop()

        # Prevent skipping practice steps if not completed
        step = self.story_manager.get_current_step()
        if step and step.step_type == StoryStepType.PRACTICE and not self.level_completed:
            return

        self.is_listening = False
        if self.story_manager.advance_step():
            self.load_step()
        
    def exit_game(self):
        self.game_active = False
        self.auto_retry_timer.stop()
        self.success_timer.stop()
        if hasattr(self, '_patronus_monitor_timer'):
            self._patronus_monitor_timer.stop()
        if self.verification_thread:
            # Disconnect any pending signals to avoid callbacks after cleanup
            try:
                self.verification_thread.finished.disconnect()
            except:
                pass
            if self.verification_thread.isRunning():
                self.verification_thread.wait(5000)  # Wait up to 5 seconds
            self.verification_thread.deleteLater()
            self.verification_thread = None
        self.is_listening = False
        self.camera_widget.stop_camera()
        if self.voice_verifier:
            self.voice_verifier.release()
            self.voice_verifier = None
        self.finished.emit()

    def closeEvent(self, event):
        self.exit_game()
        super().closeEvent(event)

