"""app/renderers/default.py — 默认渲染器（沿用现有立绘显示）。

:class:`DefaultRenderer` 是一个纯空操作（no-op）渲染器，语义为
「渲染器不接管角色显示，PetWindow 现有的 PortraitController 立绘逻辑照常工作」。

它既是未开启实验性渲染器时的默认选择，也是 MMD 等高级后端初始化失败时的
**回退目标**。因此本类必须保证：不创建任何窗口、不抛异常、不影响现有显示。
"""

from __future__ import annotations

from typing import Any

from app.renderers.base import CharacterRenderer


class DefaultRenderer(CharacterRenderer):
    """空操作渲染器：保持现有 PNG 立绘显示不变。"""

    renderer_name = "default"

    def initialize(self, app_context: dict[str, Any] | None = None) -> None:
        # 不接管显示，无需初始化任何资源。
        return None

    def is_available(self) -> bool:
        # 默认渲染器永远可用，作为最终兜底。
        return True
