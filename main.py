import json
import os
import tempfile
import time
import pathlib
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.message_components import File, Plain

@register("viewcontext_plugin", "YourName", "查看当前对话上下文内容，支持导出为文本文件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}

    async def initialize(self):
        pass

    @filter.command("viewcontext")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def viewcontext(self, event: AstrMessageEvent):
        """查看当前对话上下文并导出为文件（仅管理员）"""
        umo = event.unified_msg_origin
        conv_mgr = self.context.conversation_manager

        cid = await conv_mgr.get_curr_conversation_id(umo)
        if not cid:
            yield event.plain_result("当前没有活跃的对话。")
            return

        conv = await conv_mgr.get_conversation(umo, cid)
        if not conv or not conv.history:
            yield event.plain_result("当前上下文为空。")
            return

        history = json.loads(conv.history)

        lines = [f"对话 ID: {cid}"]
        if conv.title:
            lines.append(f"标题: {conv.title}")
        lines.append(f"消息总数: {len(history)}")
        lines.append("=" * 40)
        lines.append("")

        for i, msg in enumerate(history, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{i}] {role.upper()}")
            lines.append(str(content))
            lines.append("")

        text_content = "\n".join(lines)

        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"context_{cid[:8]}_{int(time.time())}.txt")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        target_user_id = self.config.get("target_user_id", "")

        if target_user_id:
            try:
                bot = getattr(event, "bot", None)
                if bot is None or not hasattr(bot, "send_private_msg"):
                    yield event.plain_result("当前平台不支持将文件发送给指定用户。")
                    return
                chain = MessageChain(chain=[
                    Plain(f"对话上下文已导出（共 {len(history)} 条消息）\n"),
                    File(name=f"context_{cid[:8]}.txt", file=tmp_path),
                ])
                messages = await type(event)._parse_onebot_json(chain)
                await bot.send_private_msg(user_id=int(target_user_id), message=messages)
                yield event.plain_result(f"上下文已发送给目标用户。")
            except Exception as e:
                logger.error(f"发送给目标用户失败: {e}")
                yield event.plain_result(f"发送给目标用户失败: {e}")
        else:
            result = event.make_result()
            result.message(f"当前上下文已导出（共 {len(history)} 条消息）:\n")
            result.chain.append(File(name=f"context_{cid[:8]}.txt", file=tmp_path))
            yield result

    async def terminate(self):
        pass
