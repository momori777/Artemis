"""app/renderers — 通用角色渲染后端层。

对外导出渲染器抽象接口、默认渲染器与管理器。具体重后端（如 MMD/Live2D）
由插件贡献，宿主不直接导入。
"""

from __future__ import annotations

from app.renderers.base import CharacterRenderer
from app.renderers.default import DefaultRenderer
from app.renderers.manager import RendererManager

__all__ = [
    "CharacterRenderer",
    "DefaultRenderer",
    "RendererManager",
]
