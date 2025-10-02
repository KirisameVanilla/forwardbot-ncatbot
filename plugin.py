from ncatbot.core.event import GroupMessageEvent
from ncatbot.plugin_system import (
    NcatBotPlugin,
    command_registry,
    group_filter,
    option,
    param,
    root_filter,
)
from ncatbot.utils import config, get_log

from .forward_admin_filter import ForwardAdminFilter
from .rules import ForwardRuleManager

import time


class ForwardBotPlugin(NcatBotPlugin):
    name = "ForwardBot"
    version = "0.0.1"
    author = "KirisameVanilla"

    logger = get_log("ForwardBot")

    manager = ForwardRuleManager()

    forward_command_group = command_registry.group(
        "forward", description="消息转发模块命令"
    )
    forward_rules_command_group = forward_command_group.group(
        "rules", description="转发规则管理命令"
    )
    forward_admins_command_group = forward_command_group.group(
        "admins", description="转发管理员管理命令"
    )

    forward_stats = {"success": 0, "failed": 0, "start_time": time.time()}

    async def on_load(self) -> None:
        self.rbac_manager.add_role("forward_admin")
        # 为配置的每个 admin 赋予权限
        for admin in self.manager.admins:
            self.rbac_manager.assign_role_to_user(str(admin), "forward_admin")
            self.logger.info(f"✅ 已赋予转发管理员权限: {admin}")

    @root_filter
    @forward_admins_command_group.command("add")
    @param(name="user_id", default="", help="要添加的管理员QQ号")
    async def admin_add_cmd(self, event: GroupMessageEvent, user_id: str = ""):
        """添加转发管理员"""
        if not user_id:
            await event.reply("❌ 请指定要添加的管理员QQ号")
            return
        self.rbac_manager.assign_role_to_user(user_id, "forward_admin")
        await event.reply(f"✅ 成功添加转发管理员: {user_id}")
        self.logger.info(
            f"✅ 已添加转发管理员: {user_id} (操作人: 群 {event.sender.user_id})"
        )

    @forward_command_group.command("stats")
    @option(short_name="v", long_name="verbose", help="启用详细模式")
    async def stats_cmd(self, event: GroupMessageEvent, verbose: bool = False):
        """查看转发统计信息"""
        try:
            # 转发统计
            total_attempts = (
                self.forward_stats["success"] + self.forward_stats["failed"]
            )
            runtime = time.time() - self.forward_stats["start_time"]
            success_rate = (
                (self.forward_stats["success"] / total_attempts * 100)
                if total_attempts > 0
                else 0
            )

            # 规则统计
            rule_stats = self.manager.get_statistics()

            stats_text = f"""📊 转发机器人统计信息
            
    🚀 转发统计：
    • 成功转发：{self.forward_stats["success"]} 次
    • 失败转发：{self.forward_stats["failed"]} 次
    • 总计尝试：{total_attempts} 次
    • 成功率：{success_rate:.1f}%
    • 运行时间：{runtime / 60:.1f} 分钟

    📋 规则统计：
    • 总规则数：{rule_stats["total_rules"]} 条
    • 已启用：{rule_stats["enabled_rules"]} 条
    • 已禁用：{rule_stats["disabled_rules"]} 条
    • 监听群数：{rule_stats["monitored_groups"]} 个
    • 目标群数：{rule_stats["target_groups"]} 个"""

            # 如果启用详细模式，添加额外信息
            if verbose:
                stats_text += f"""
                
    🔍 详细信息：
    • 启动时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.forward_stats["start_time"]))}
    • 平均成功率：{success_rate:.2f}%
    • 监听的源群：{", ".join(map(str, rule_stats["source_groups_list"][:5]))}{"..." if len(rule_stats["source_groups_list"]) > 5 else ""}
    • 转发目标群：{", ".join(map(str, rule_stats["target_groups_list"][:5]))}{"..." if len(rule_stats["target_groups_list"]) > 5 else ""}"""

            await event.reply(stats_text)
            self.logger.info(f"📊 用户查看统计信息：群 {event.group_id}")

        except Exception as e:
            self.logger.error(f"❌ 处理统计命令时出错: {e}")
            await event.reply("❌ 获取统计信息失败")

    @ForwardAdminFilter()
    @forward_rules_command_group.command("list")
    @option(short_name="d", long_name="detailed", help="启用详细格式")
    async def rules_list_cmd(self, event: GroupMessageEvent, detailed: bool = False):
        """查看转发规则列表"""
        try:
            if not self.manager.rules:
                await event.reply("📋 当前没有配置任何转发规则")
                return

            rules_text = "📋 转发规则列表：\n\n"

            for i, rule in enumerate(self.manager.rules, 1):
                status = "🟢 启用" if rule.enabled else "🔴 禁用"
                rule_type = "前缀匹配" if rule.type == "prefix" else "关键词匹配"

                if detailed:
                    # 详细格式
                    rules_text += f"{i}. {rule.name}\n"
                    rules_text += f"   状态：{status}\n"
                    rules_text += f"   类型：{rule_type}\n"
                    rules_text += f"   关键词：{', '.join(rule.keywords)}\n"
                    rules_text += (
                        f"   源群：{', '.join(map(str, rule.source_groups))}\n"
                    )
                    rules_text += (
                        f"   目标群：{', '.join(map(str, rule.target_groups))}\n"
                    )
                    rules_text += f"   转发前缀：{rule.forward_prefix}\n\n"
                else:
                    # 简单格式（默认）
                    rules_text += f"{i}. {rule.name}\n"
                    rules_text += f"   状态：{status}\n"
                    rules_text += f"   类型：{rule_type}\n"
                    rules_text += f"   关键词：{', '.join(rule.keywords[:3])}{'...' if len(rule.keywords) > 3 else ''}\n"
                    rules_text += f"   源群：{len(rule.source_groups)} 个\n"
                    rules_text += f"   目标群：{len(rule.target_groups)} 个\n\n"

            # 如果消息太长，截断并提示
            if len(rules_text) > 1000:
                rules_text = rules_text[:950] + "...\n\n（规则过多，仅显示部分）"

            await event.reply(rules_text.strip())
            self.logger.info(f"📋 用户查看规则列表：群 {event.group_id}")

        except Exception as e:
            self.logger.error(f"❌ 处理规则列表命令时出错: {e}")
            await event.reply("❌ 获取规则列表失败")

    async def rule_add_cmd(self, event: GroupMessageEvent):
        """添加转发规则"""
        await event.reply("🚧 规则添加功能正在开发中...")

    @ForwardAdminFilter()
    @forward_rules_command_group.command("delete")
    @param(name="rule_name", default="", help="要删除的规则名称")
    @option(short_name="f", long_name="force", help="启用强制删除模式")
    async def rule_delete_cmd(
        self, event: GroupMessageEvent, rule_name: str, force: bool = False
    ):
        """删除转发规则"""
        try:
            if not rule_name:
                await event.reply("❌ 请指定要删除的规则名称")
                return

            # 检查规则是否存在
            rule = self.manager.get_rule(rule_name)
            if not rule:
                await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
                return

            # 如果不是强制模式，显示规则信息进行确认
            if not force:
                rule_info = f"""⚠️ 即将删除规则 '{rule_name}'：
                
• 类型：{"前缀匹配" if rule.type == "prefix" else "关键词匹配"}
• 状态：{"🟢 启用" if rule.enabled else "🔴 禁用"}
• 关键词：{", ".join(rule.keywords[:3])}{"..." if len(rule.keywords) > 3 else ""}
• 源群数：{len(rule.source_groups)} 个
• 目标群数：{len(rule.target_groups)} 个

请使用 --force 选项确认删除"""
                await event.reply(rule_info)
                return

            # 删除规则
            if self.manager.remove_rule(rule_name):
                await event.reply(f"✅ 成功删除规则 '{rule_name}'")
                self.logger.info(f"🗑️ 规则已删除：{rule_name} (群 {event.group_id})")

                # 重新加载配置以确保一致性
                self.manager.load_config()
            else:
                await event.reply(f"❌ 删除规则 '{rule_name}' 失败")

        except Exception as e:
            self.logger.error(f"❌ 处理删除规则命令时出错: {e}")
            await event.reply("❌ 删除规则失败")

    @ForwardAdminFilter()
    @forward_rules_command_group.command("enable")
    @param(name="rule_name", default="", help="要启用的规则名称")
    async def rule_enable_cmd(self, event: GroupMessageEvent, rule_name: str = ""):
        """启用转发规则"""
        try:
            if not rule_name:
                await event.reply("❌ 请指定要启用的规则名称")
                return

            # 检查规则是否存在
            rule = self.manager.get_rule(rule_name)
            if not rule:
                await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
                return

            if rule.enabled:
                await event.reply(f"ℹ️ 规则 '{rule_name}' 已经是启用状态")
                return

            # 启用规则
            if self.manager.enable_rule(rule_name):
                await event.reply(f"✅ 成功启用规则 '{rule_name}'")
                self.logger.info(f"🟢 规则已启用：{rule_name} (群 {event.group_id})")
            else:
                await event.reply(f"❌ 启用规则 '{rule_name}' 失败")

        except Exception as e:
            self.logger.error(f"❌ 处理启用规则命令时出错: {e}")
            await event.reply("❌ 启用规则失败")

    @ForwardAdminFilter()
    @forward_rules_command_group.command("disable")
    @param(name="rule_name", default="", help="要禁用的规则名称")
    async def rule_disable_cmd(self, event: GroupMessageEvent, rule_name: str):
        """禁用转发规则"""
        try:
            if not rule_name:
                await event.reply("❌ 请指定要禁用的规则名称")
                return

            # 检查规则是否存在
            rule = self.manager.get_rule(rule_name)
            if not rule:
                await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
                return

            if not rule.enabled:
                await event.reply(f"ℹ️ 规则 '{rule_name}' 已经是禁用状态")
                return

            # 禁用规则
            if self.manager.disable_rule(rule_name):
                await event.reply(f"✅ 成功禁用规则 '{rule_name}'")
                self.logger.info(f"🔴 规则已禁用：{rule_name} (群 {event.group_id})")
            else:
                await event.reply(f"❌ 禁用规则 '{rule_name}' 失败")

        except Exception as e:
            self.logger.error(f"❌ 处理禁用规则命令时出错: {e}")
            await event.reply("❌ 禁用规则失败")

    def safe_forward_message(
        self, target_group: int, message_id: str, rule_name: str, max_retries: int = 2
    ) -> bool:
        """
        安全的消息转发函数，带有重试机制

        Args:
            target_group: 目标群号
            message_id: 消息ID
            rule_name: 规则名称
            max_retries: 最大重试次数

        Returns:
            bool: 转发是否成功
        """
        for attempt in range(max_retries + 1):
            try:
                self.api.forward_group_single_msg_sync(target_group, message_id)
                self.api.set_msg_emoji_like_sync(message_id, 124, True)

                self.forward_stats["success"] += 1
                if attempt > 0:
                    self.logger.info(
                        f"✅ 消息转发成功 (重试第{attempt}次): 群{target_group}"
                    )
                else:
                    self.logger.info(f"✅ 消息转发成功: 群{target_group}")
                return True
            except AttributeError as e:
                self.logger.error(
                    f"❌ AttributeError: 群{target_group}, 规则{rule_name}"
                )
                self.logger.error(f"   错误: {e}")
                self.logger.error(
                    "   这通常表示目标群不存在、机器人不在群中、或消息已撤回"
                )
                break  # AttributeError 通常不需要重试

            except Exception as e:
                self.logger.error(
                    f"❌ 转发异常: 群{target_group}, 规则{rule_name} (尝试 {attempt + 1}/{max_retries + 1})"
                )
                self.logger.error(f"   错误: {e}")

            # 如果不是最后一次尝试，等待一下再重试
            if attempt < max_retries:
                time.sleep(0.5)

        self.forward_stats["failed"] += 1
        return False

    @group_filter
    async def onGroupMessageReceived(self, event: GroupMessageEvent):
        message_id = event.message_id
        message = "".join(seg.text for seg in event.message.filter_text())

        if message.startswith("/"):
            return

        sender_uin = event.sender.user_id
        if sender_uin == config.bt_uin:
            self.logger.info(f"🟢 过滤掉来自自身的消息: {sender_uin}")
            return
        source_group = int(event.group_id)

        # 查找匹配的规则
        matching_rules = self.manager.find_matching_rules(message, source_group)

        if not matching_rules:
            # 只在调试模式下记录无匹配规则的消息
            self.logger.debug(f"📝 群 {source_group} 消息无匹配规则: {message[:50]}")
            return

        self.logger.info(
            f"📝 群 {source_group} 消息匹配到 {len(matching_rules)} 条规则: {message[:50]}"
        )

        forward_tasks = []
        for rule in matching_rules:
            for target_group in rule.target_groups:
                if rule.can_forward_to(source_group, target_group):
                    self.logger.info(
                        f"🚀 开始转发: {source_group} -> {target_group} (规则: {rule.name})"
                    )
                    success = self.safe_forward_message(
                        target_group, message_id, rule.name
                    )
                    forward_tasks.append((target_group, success))
                else:
                    self.logger.debug(
                        f"🚫 规则 {rule.name} 不允许从 {source_group} 转发到 {target_group}"
                    )

        # 统计结果
        successful_forwards = sum(1 for _, success in forward_tasks if success)
        total_forwards = len(forward_tasks)

        if total_forwards > 0:
            self.logger.info(
                f"📊 转发完成: {successful_forwards}/{total_forwards} 成功"
            )

            # 每100次转发输出一次统计信息
            total_attempts = (
                self.forward_stats["success"] + self.forward_stats["failed"]
            )
            if total_attempts > 0 and total_attempts % 100 == 0:
                runtime = time.time() - self.forward_stats["start_time"]
                success_rate = self.forward_stats["success"] / total_attempts * 100
                self.logger.info(
                    f"📊 转发统计: 成功率 {success_rate:.1f}% ({self.forward_stats['success']}/{total_attempts}), 运行时间 {runtime:.0f}秒"
                )
