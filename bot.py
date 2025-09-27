from ncatbot.core import BotClient
from ncatbot.utils import config
from ncatbot.core.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.core.api import BotAPI
from rules import ForwardRuleManager
import logging
import time

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forward_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 基础配置
bot: BotClient = BotClient()
api: BotAPI = bot.api
manager = ForwardRuleManager()

# 转发统计
forward_stats = {
    'success': 0,
    'failed': 0,
    'start_time': time.time()
}

# 检查配置是否正确
if not manager.rules:
    logger.warning("⚠️ 未找到任何转发规则，请检查 forward_config.yaml 配置文件")
else:
    enabled_rules = manager.get_enabled_rules()
    logger.info(f"📋 已加载 {len(manager.rules)} 条规则，其中 {len(enabled_rules)} 条已启用")


async def handle_forward_command(event: GroupMessageEvent, message: str):
    """
    处理转发命令
    
    Args:
        event: 群消息事件
        message: 命令消息内容
    """
    parts = message.split()
    if len(parts) < 2:
        await event.reply("❌ 命令格式错误。可用命令：\n/forward stats\n/forward rules\n/forward rules add\n/forward rules delete <name>\n/forward rules enable <name>\n/forward rules disable <name>")
        return
    
    command = parts[1].lower()
    
    if command == "stats":
        await handle_stats_command(event)
    elif command == "rules":
        if len(parts) == 2:
            await handle_rules_command(event)
        elif len(parts) >= 3:
            subcommand = parts[2].lower()
            if subcommand == "add":
                await handle_rules_add_command(event)
            elif subcommand == "delete" and len(parts) >= 4:
                rule_name = " ".join(parts[3:])
                await handle_rules_delete_command(event, rule_name)
            elif subcommand == "enable" and len(parts) >= 4:
                rule_name = " ".join(parts[3:])
                await handle_rules_enable_command(event, rule_name)
            elif subcommand == "disable" and len(parts) >= 4:
                rule_name = " ".join(parts[3:])
                await handle_rules_disable_command(event, rule_name)
            else:
                await event.reply("❌ 未知的规则命令。可用命令：add, delete <name>, enable <name>, disable <name>")
        else:
            await event.reply("❌ 规则命令缺少参数")
    else:
        await event.reply("❌ 未知命令。可用命令：stats, rules")


async def handle_stats_command(event: GroupMessageEvent):
    """处理统计命令"""
    try:
        # 转发统计
        total_attempts = forward_stats['success'] + forward_stats['failed']
        runtime = time.time() - forward_stats['start_time']
        success_rate = (forward_stats['success'] / total_attempts * 100) if total_attempts > 0 else 0
        
        # 规则统计
        rule_stats = manager.get_statistics()
        
        stats_text = f"""📊 转发机器人统计信息
        
🚀 转发统计：
• 成功转发：{forward_stats['success']} 次
• 失败转发：{forward_stats['failed']} 次
• 总计尝试：{total_attempts} 次
• 成功率：{success_rate:.1f}%
• 运行时间：{runtime/60:.1f} 分钟

📋 规则统计：
• 总规则数：{rule_stats['total_rules']} 条
• 已启用：{rule_stats['enabled_rules']} 条
• 已禁用：{rule_stats['disabled_rules']} 条
• 监听群数：{rule_stats['monitored_groups']} 个
• 目标群数：{rule_stats['target_groups']} 个"""

        await event.reply(stats_text)
        logger.info(f"📊 用户查看统计信息：群 {event.group_id}")
        
    except Exception as e:
        logger.error(f"❌ 处理统计命令时出错: {e}")
        await event.reply("❌ 获取统计信息失败")


async def handle_rules_command(event: GroupMessageEvent):
    """处理规则列表命令"""
    try:
        if not manager.rules:
            await event.reply("📋 当前没有配置任何转发规则")
            return
        
        rules_text = "📋 转发规则列表：\n\n"
        
        for i, rule in enumerate(manager.rules, 1):
            status = "🟢 启用" if rule.enabled else "🔴 禁用"
            rule_type = "前缀匹配" if rule.type == "prefix" else "关键词匹配"
            
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
        logger.info(f"📋 用户查看规则列表：群 {event.group_id}")
        
    except Exception as e:
        logger.error(f"❌ 处理规则列表命令时出错: {e}")
        await event.reply("❌ 获取规则列表失败")


async def handle_rules_add_command(event: GroupMessageEvent):
    """处理添加规则命令"""
    await event.reply("🚧 规则添加功能正在开发中...")
    pass


async def handle_rules_delete_command(event: GroupMessageEvent, rule_name: str):
    """处理删除规则命令"""
    try:
        if not rule_name:
            await event.reply("❌ 请指定要删除的规则名称")
            return
        
        # 检查规则是否存在
        rule = manager.get_rule(rule_name)
        if not rule:
            await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
            return
        
        # 删除规则
        if manager.remove_rule(rule_name):
            await event.reply(f"✅ 成功删除规则 '{rule_name}'")
            logger.info(f"🗑️ 规则已删除：{rule_name} (群 {event.group_id})")
            
            # 重新加载配置以确保一致性
            manager.load_config()
        else:
            await event.reply(f"❌ 删除规则 '{rule_name}' 失败")
            
    except Exception as e:
        logger.error(f"❌ 处理删除规则命令时出错: {e}")
        await event.reply("❌ 删除规则失败")


async def handle_rules_enable_command(event: GroupMessageEvent, rule_name: str):
    """处理启用规则命令"""
    try:
        if not rule_name:
            await event.reply("❌ 请指定要启用的规则名称")
            return
        
        # 检查规则是否存在
        rule = manager.get_rule(rule_name)
        if not rule:
            await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
            return
        
        if rule.enabled:
            await event.reply(f"ℹ️ 规则 '{rule_name}' 已经是启用状态")
            return
        
        # 启用规则
        if manager.enable_rule(rule_name):
            await event.reply(f"✅ 成功启用规则 '{rule_name}'")
            logger.info(f"🟢 规则已启用：{rule_name} (群 {event.group_id})")
        else:
            await event.reply(f"❌ 启用规则 '{rule_name}' 失败")
            
    except Exception as e:
        logger.error(f"❌ 处理启用规则命令时出错: {e}")
        await event.reply("❌ 启用规则失败")


async def handle_rules_disable_command(event: GroupMessageEvent, rule_name: str):
    """处理禁用规则命令"""
    try:
        if not rule_name:
            await event.reply("❌ 请指定要禁用的规则名称")
            return
        
        # 检查规则是否存在
        rule = manager.get_rule(rule_name)
        if not rule:
            await event.reply(f"❌ 未找到名为 '{rule_name}' 的规则")
            return
        
        if not rule.enabled:
            await event.reply(f"ℹ️ 规则 '{rule_name}' 已经是禁用状态")
            return
        
        # 禁用规则
        if manager.disable_rule(rule_name):
            await event.reply(f"✅ 成功禁用规则 '{rule_name}'")
            logger.info(f"🔴 规则已禁用：{rule_name} (群 {event.group_id})")
        else:
            await event.reply(f"❌ 禁用规则 '{rule_name}' 失败")
            
    except Exception as e:
        logger.error(f"❌ 处理禁用规则命令时出错: {e}")
        await event.reply("❌ 禁用规则失败")


def safe_forward_message(target_group: int, message_id: str, rule_name: str, max_retries: int = 2) -> bool:
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
            result = api.forward_group_single_msg_sync(target_group, message_id)
            
            if result:
                forward_stats['success'] += 1
                if attempt > 0:
                    logger.info(f"✅ 消息转发成功 (重试第{attempt}次): 群{target_group}")
                else:
                    logger.info(f"✅ 消息转发成功: 群{target_group}")
                return True
            else:
                logger.warning(f"⚠️ API返回空结果: 群{target_group} (尝试 {attempt + 1}/{max_retries + 1})")
                
        except AttributeError as e:
            logger.error(f"❌ AttributeError: 群{target_group}, 规则{rule_name}")
            logger.error(f"   错误: {e}")
            logger.error("   这通常表示目标群不存在、机器人不在群中、或消息已撤回")
            break  # AttributeError 通常不需要重试
            
        except Exception as e:
            logger.error(f"❌ 转发异常: 群{target_group}, 规则{rule_name} (尝试 {attempt + 1}/{max_retries + 1})")
            logger.error(f"   错误: {e}")
            
        # 如果不是最后一次尝试，等待一下再重试
        if attempt < max_retries:
            time.sleep(0.5)
    
    forward_stats['failed'] += 1
    return False


@bot.on_group_message
async def onGroupMessageReceived(event: GroupMessageEvent):
    message_id = event.message_id
    message = "".join(seg.text for seg in event.message.filter_text())
    sender_uin = event.sender.user_id
    if sender_uin == config.bt_uin:
        logger.info(f"🟢 过滤掉来自自身的消息: {sender_uin}")
        return
    source_group = int(event.group_id)
    
    # 检查是否为命令
    if message.startswith('/forward'):
        await handle_forward_command(event, message.strip())
        return
    
    # 查找匹配的规则
    matching_rules = manager.find_matching_rules(message, source_group)
    
    if not matching_rules:
        # 只在调试模式下记录无匹配规则的消息
        logger.debug(f"📝 群 {source_group} 消息无匹配规则: {message[:50]}")
        return
    
    logger.info(f"📝 群 {source_group} 消息匹配到 {len(matching_rules)} 条规则: {message[:50]}")
    
    forward_tasks = []
    for rule in matching_rules:
        for target_group in rule.target_groups:
            if rule.can_forward_to(source_group, target_group):
                logger.info(f"🚀 开始转发: {source_group} -> {target_group} (规则: {rule.name})")
                success = safe_forward_message(target_group, message_id, rule.name)
                forward_tasks.append((target_group, success))
            else:
                logger.debug(f"🚫 规则 {rule.name} 不允许从 {source_group} 转发到 {target_group}")
    
    # 统计结果
    successful_forwards = sum(1 for _, success in forward_tasks if success)
    total_forwards = len(forward_tasks)
    
    if total_forwards > 0:
        logger.info(f"📊 转发完成: {successful_forwards}/{total_forwards} 成功")
        
        # 每100次转发输出一次统计信息
        total_attempts = forward_stats['success'] + forward_stats['failed']
        if total_attempts > 0 and total_attempts % 100 == 0:
            runtime = time.time() - forward_stats['start_time']
            success_rate = forward_stats['success'] / total_attempts * 100
            logger.info(f"� 转发统计: 成功率 {success_rate:.1f}% ({forward_stats['success']}/{total_attempts}), 运行时间 {runtime:.0f}秒")


@bot.on_private_message
def greet_private(event: PrivateMessageEvent):
    # 同步处理器也可用：
    event.reply_sync("收到私聊（同步回复）")


bot.run_frontend(debug=True)
