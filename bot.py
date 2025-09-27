from ncatbot.core import BotClient
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
    source_group = int(event.group_id)
    
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
