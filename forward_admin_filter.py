from ncatbot.plugin_system.builtin_plugin.unified_registry.filter_system import (
    BaseFilter,
)
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import status


class ForwardAdminFilter(BaseFilter):
    """转发管理员过滤器"""

    def __init__(self):
        super().__init__("forward_admin")

    def check(self, event: BaseMessageEvent) -> bool:
        return status.global_access_manager.user_has_role(
            event.user_id, "forward_admin"
        )
