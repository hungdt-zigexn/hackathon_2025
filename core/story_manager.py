from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from core.spell_engine import SpellType


class StoryStepType(Enum):
    """Different phases of the guided story."""

    EXPLANATION = "explanation"
    PRACTICE = "practice"


@dataclass
class StoryStep:
    id: int
    title: str
    description: str
    step_type: StoryStepType
    required_spell: Optional[SpellType]
    success_message: Optional[str] = None
    next_step_id: Optional[int] = None


class StoryManager:
    def __init__(self):
        self.current_step_id = 1
        self.steps: Dict[int, StoryStep] = self._init_steps()

    def _init_steps(self) -> Dict[int, StoryStep]:
        return {
            # Lumos briefing + practice
            1: StoryStep(
                id=1,
                title="Giới thiệu Lumos",
                description=(
                    "Bạn đứng trong hành lang bị bóng tối bao phủ. Bài học đầu tiên rất đơn giản: "
                    "tập trung vào đầu đũa phép, hình dung ánh sáng ấm áp, và nhớ rằng ngay cả một tia lửa nhỏ "
                    "cũng có thể xua tan bóng tối. Đây là Lumos."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.LUMOS,
                next_step_id=2,
            ),
            2: StoryStep(
                id=2,
                title="Thực hành Lumos",
                description=(
                    "Đã đến lúc chuyển lý thuyết thành hành động. Hít thở đều đặn và nói 'Lumos' để thắp sáng con đường."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.LUMOS,
                success_message="Tuyệt vời! Hành lang bừng sáng và một cánh cửa gỗ sồi hiện ra phía trước.",
                next_step_id=3,
            ),
            # Wingardium Leviosa briefing + practice
            3: StoryStep(
                id=3,
                title="Thử thách của người xứng đáng",
                description=(
                    "Giữa sân huấn luyện, một chiếc búa cổ đại nằm bất động trên bệ đá. "
                    "Người hướng dẫn nhìn bạn và nói: không phải sức mạnh, mà là sự tập trung và ý chí "
                    "mới quyết định liệu bạn có thể nâng nó lên hay không."
                    "Wingardium Leviosa không chỉ là phép bay lơ lửng—"
                    "đó là bài kiểm tra xem bạn có thực sự xứng đáng để điều khiển ma thuật hay không."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.WINGARDIUM_LEVIOSA,
                next_step_id=4,
            ),
            4: StoryStep(
                id=4,
                title="Nâng búa thử thách",
                description=(
                    "Tập trung tinh thần, giữ tay vững vàng và thi triển 'Wingardium Leviosa'. "
                    "Nếu tâm trí bạn đủ thuần khiết và ý chí đủ mạnh, chiếc búa sẽ nhấc lên khỏi mặt đất."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.WINGARDIUM_LEVIOSA,
                success_message=(
                    "Chiếc búa rung nhẹ… rồi từ từ bay lên trong không trung. "
                    "Bạn đã chứng minh mình là người xứng đáng!"
                ),
                next_step_id=5,
            ),
            # Vera Verto briefing + practice
            5: StoryStep(
                id=5,
                title="Giới thiệu Vera Verto",
                description=(
                    "Chào mừng đến với lớp Biến hình! Bài học này là Vera Verto - phép biến đổi vật thể. "
                    "Để thực hiện phép này, bạn cần chạm đũa phép vào vật thể, sau đó chỉ đũa về phía nó "
                    "và đọc to 'Vera Verto'. Một làn sương mờ sẽ bao phủ vật thể và biến đổi nó. "
                    "Hãy nhớ: tư thế và chuyển động đũa phép rất quan trọng!"
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.VERA_VERTO,
                next_step_id=6,
            ),
            6: StoryStep(
                id=6,
                title="Thực hành Vera Verto",
                description=(
                    "Đã đến lúc thực hành! Trước mặt bạn có một vật thể cần được biến đổi. "
                    "Chạm đũa phép vào vật thể, chỉ đũa về phía nó và nói 'Vera Verto' để bắt đầu phép biến đổi."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.VERA_VERTO,
                success_message="Tuyệt vời! Vật thể đã được biến đổi thành công với làn sương mờ và ánh sáng ma thuật!",
                next_step_id=7,
            ),
            # Expecto Patronum briefing + practice
            7: StoryStep(
                id=7,
                title="Triệu hồi Patronus",
                description=(
                    "Không giống những phép thuật khác, Expecto Patronum không dựa vào lời nói đơn thuần. "
                    "Bạn phải vẽ một ký hiệu đặc biệt trong không khí, theo đúng hướng dẫn."
                    "Mỗi nét vẽ là một dòng chảy ma thuật. Khi hoàn chỉnh, ký hiệu sẽ mở cánh cổng "
                    "triệu hồi Thần hộ mệnh—hiện thân của ký ức hạnh phúc và sức mạnh nội tâm của bạn."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.EXPECTO_PATRONUM,
                next_step_id=8,
            ),
            8: StoryStep(
                id=8,
                title="Thực hành Expecto Patronum",
                description=(
                    "Thi triển 'Expecto Patronum' và vẽ ký hiệu theo đúng hướng dẫn bằng đũa phép."
                    "Nếu các nét vẽ chính xác và liền mạch, Thần hộ mệnh sẽ được triệu hồi."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.EXPECTO_PATRONUM,
                success_message=(
                    "🌟 Thần hộ mệnh đã được triệu hồi! Ánh bạc bao quanh bạn 🌟"
                ),
                next_step_id=None,
            ),
        }

    def get_current_step(self) -> Optional[StoryStep]:
        return self.steps.get(self.current_step_id)

    def advance_step(self) -> bool:
        """Advance to the next step. Returns True if there is a next step."""
        current = self.get_current_step()
        if current and current.next_step_id:
            self.current_step_id = current.next_step_id
            return True
        return False

    def skip_step(self) -> bool:
        """Skip the current step and advance to the next step. Returns True if there is a next step."""
        current = self.get_current_step()
        if current and current.next_step_id:
            self.current_step_id = current.next_step_id
            return True
        return False

    def go_back(self) -> bool:
        """Go back to the previous step. Returns True if there is a previous step."""
        if self.current_step_id > 1:
            self.current_step_id -= 1
            return True
        return False

    def reset(self):
        self.current_step_id = 1

