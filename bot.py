from ncatbot.core import BotClient
from ncatbot.core.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.core.api import BotAPI
from rules import ForwardRuleManager


# 基础配置（示例）
bot: BotClient = BotClient()
api: BotAPI = bot.api
manager = ForwardRuleManager()


@bot.on_group_message
async def onGroupMessageReceived(event: GroupMessageEvent):
    message_id = event.message_id
    message = "".join(seg.text for seg in event.message.filter_text())
    source_group = int(event.group_id)
    matching_rules = manager.find_matching_rules(message, source_group)
    for rule in matching_rules:
        for target_group in rule.target_groups:
            if rule.can_forward_to(source_group, target_group):
                api.forward_group_single_msg_sync(target_group, message_id)


@bot.on_private_message
def greet_private(event: PrivateMessageEvent):
    # 同步处理器也可用：
    event.reply_sync("收到私聊（同步回复）")


bot.run_frontend(debug=True)
