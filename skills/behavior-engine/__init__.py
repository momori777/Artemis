"""
Behavior Engine Package

每个角色的状态存放在 memory/role_play/<char>/relationship.json。
"""

from .engine import (
    CharacterState,
    RelationshipScore,
    ConflictState,
    HormoneState,
    load_state,
    save_state,
    update_state,
    reset_state,
    get_state_path,
)
from .hormones import compute_hormones, get_hormone_status
from .conflict import escalate_from_mood, soften_from_mood, conflict_prompt_fragment, active_conflict
from .stages import decide_stage_transition, should_run_check, get_stage_label, get_stage_defaults
from .behavior_tick import behavior_tick, is_asleep, is_night_awake
from .online_tick import decide_online
from .daily_life import generate_daily_life, current_block, daily_life_prompt

__all__ = [
    "CharacterState",
    "RelationshipScore",
    "ConflictState",
    "HormoneState",
    "load_state",
    "save_state",
    "update_state",
    "reset_state",
    "get_state_path",
    "compute_hormones",
    "get_hormone_status",
    "escalate_from_mood",
    "soften_from_mood",
    "conflict_prompt_fragment",
    "active_conflict",
    "decide_stage_transition",
    "should_run_check",
    "get_stage_label",
    "get_stage_defaults",
    "behavior_tick",
    "is_asleep",
    "is_night_awake",
    "decide_online",
    "generate_daily_life",
    "current_block",
    "daily_life_prompt",
]
