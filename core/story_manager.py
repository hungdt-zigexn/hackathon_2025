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
            # Vera Verto briefing + practice
            1: StoryStep(
                id=1,
                title="Giới thiệu Vera Verto",
                description=(
                    "Chào mừng đến với lớp Biến hình! Bài học đầu tiên là Vera Verto - phép biến đổi vật thể. "
                    "Để thực hiện phép này, bạn cần chạm đũa phép ba lần vào vật thể, sau đó chỉ đũa về phía nó "
                    "và đọc to 'Vera Verto'. Một làn sương mờ sẽ bao phủ vật thể và biến đổi nó. "
                    "Hãy nhớ: tư thế và chuyển động đũa phép rất quan trọng!"
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.VERA_VERTO,
                next_step_id=2,
            ),
            2: StoryStep(
                id=2,
                title="Thực hành Vera Verto",
                description=(
                    "Đã đến lúc thực hành! Trước mặt bạn có một vật thể cần được biến đổi. "
                    "Chạm đũa phép ba lần vào vật thể, chỉ đũa về phía nó và nói 'Vera Verto' để bắt đầu phép biến đổi."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.VERA_VERTO,
                success_message="Tuyệt vời! Vật thể đã được biến đổi thành công với làn sương mờ và ánh sáng ma thuật!",
                next_step_id=3,
            ),
            # Lumos briefing + practice
            3: StoryStep(
                id=3,
                title="Giới thiệu Lumos",
                description=(
                    "Bạn đứng trong hành lang bị bóng tối bao phủ. Bài học đầu tiên rất đơn giản: "
                    "tập trung vào đầu đũa phép, hình dung ánh sáng ấm áp, và nhớ rằng ngay cả một tia lửa nhỏ "
                    "cũng có thể xua tan bóng tối. Đây là Lumos."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.LUMOS,
                next_step_id=4,
            ),
            4: StoryStep(
                id=4,
                title="Thực hành Lumos",
                description=(
                    "Đã đến lúc chuyển lý thuyết thành hành động. Hít thở đều đặn và nói 'Lumos' để thắp sáng con đường."
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.LUMOS,
                success_message="Tuyệt vời! Hành lang bừng sáng và một cánh cửa gỗ sồi hiện ra phía trước.",
                next_step_id=5,
            ),
            # Wingardium Leviosa briefing + practice
            5: StoryStep(
                id=5,
                title="Bài học Bay lơ lửng",
                description=(
                    "Ngay bên ngoài, một đống đá chặn đường của bạn. Bay lơ lửng là về sự cân bằng—chuyển động có kiểm soát, "
                    "một cú vung nhẹ nhàng, và giọng nói tự tin dẫn dắt ma thuật."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.WINGARDIUM_LEVIOSA,
                next_step_id=6,
            ),
            6: StoryStep(
                id=6,
                title="Thực hành Wingardium Leviosa",
                description="Nâng những viên đá lên cao bằng 'Wingardium Leviosa' và dọn sạch sân.",
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.WINGARDIUM_LEVIOSA,
                success_message="Những viên đá bay sang một bên một cách uyển chuyển. Sân đã được dọn sạch—hoàn thành bài tập!",
                next_step_id=7,
            ),
            # Expecto Patronum briefing + practice
            7: StoryStep(
                id=7,
                title="Triệu hồi Patronus",
                description=(
                    "Trong Đại sảnh, bạn học phép phòng thủ mạnh nhất. "
                    "Expecto Patronum triệu hồi một vệ thần từ ký ức hạnh phúc nhất của bạn. "
                    "Vẽ một hình trong không khí bằng đũa phép, và Patronus của bạn sẽ hiện hình—"
                    "một quả bóng, một con mèo, một trái tim, một chiếc pizza, một ngôi sao, hoặc một cây đũa phép. "
                    "Hãy nghĩ về ký ức hạnh phúc nhất và để đũa phép dẫn dắt ma thuật."
                ),
                step_type=StoryStepType.EXPLANATION,
                required_spell=SpellType.EXPECTO_PATRONUM,
                next_step_id=8,
            ),
            8: StoryStep(
                id=8,
                title="Thực hành Expecto Patronum",
                description=(
                    "Thi triển 'Expecto Patronum' và vẽ Patronus của bạn trong không khí bằng đũa phép. "
                    "Bạn có 5 giây để hoàn thành bản vẽ. Tập trung vào ký ức hạnh phúc nhất của bạn!"
                ),
                step_type=StoryStepType.PRACTICE,
                required_spell=SpellType.EXPECTO_PATRONUM,
                success_message="Tuyệt vời! Patronus của bạn đã hiện hình và toả sáng với ánh bạc!",
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

    def reset(self):
        self.current_step_id = 1

