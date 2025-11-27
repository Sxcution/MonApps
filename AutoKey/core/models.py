from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

class StepType(Enum):
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    WAIT_IMAGE = "wait_image"
    UNDEFINED = "undefined"

@dataclass
class MacroStep:
    id: int
    type: StepType
    params: Dict[str, Any] = field(default_factory=dict)
