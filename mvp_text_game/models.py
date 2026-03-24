from dataclasses import dataclass, field
from typing import List


@dataclass
class NPC:
    name: str
    favorability: int = 0
    state: str = "中立"
    preference: str = ""
    psychology: str = ""


@dataclass
class Choice:
    id: str
    text: str
    type: str  # A/B/C


@dataclass
class GameState:
    charm: int = 3
    wealth: int = 5
    reputation: int = 2
    npcs: List[NPC] = field(default_factory=list)
    story_log: List[str] = field(default_factory=list)
    scene: str = ""
    current_event: str = ""
    turn: int = 0
    choices: List[Choice] = field(default_factory=list)
