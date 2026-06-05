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

    def _check_permission(self, event: AstrMessageEvent):
        target_user_id = self.config.get("target_user_id", "")
        if not target_user_id:
            return False, "请在插件配置中设置 target_user_id 以指定接收用户。"
        sender_id = event.get_sender_id()
        if not sender_id:
            return False, "无法获取发送者身份信息。"
        if sender_id != target_user_id:
            return False, "您没有权限执行此操作。"
        return True, ""

    async def _send_file(self, event: AstrMessageEvent, name: str, tmp_path: str, msg_count: int):
        target_user_id = self.config.get("target_user_id", "")
        try:
            bot = getattr(event, "bot", None)
            if bot is None or not hasattr(bot, "send_private_msg"):
                yield event.plain_result("当前平台不支持将文件发送给指定用户。")
                return
            chain = MessageChain(chain=[
                Plain(f"{name} 已导出（共 {msg_count} 条消息）\n"),
                File(name=os.path.basename(tmp_path), file=tmp_path),
            ])
            messages = await type(event)._parse_onebot_json(chain)
            await bot.send_private_msg(user_id=int(target_user_id), message=messages)
            yield event.plain_result(f"{name} 已发送给目标用户。")
        except Exception as e:
            logger.error(f"发送给目标用户失败: {e}")
            yield event.plain_result(f"发送给目标用户失败: {e}")

    @filter.command("viewcontext")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def viewcontext(self, event: AstrMessageEvent):
        """查看当前对话上下文并导出为文件（仅管理员）"""
        allowed, msg = self._check_permission(event)
        if not allowed:
            yield event.plain_result(msg)
            return
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

        output_format = self.config.get("output_format", "text")

        if output_format == "json":
            json_obj = {
                "conversation_id": cid,
                "title": conv.title or "",
                "total_messages": len(history),
                "messages": history,
            }
            content = json.dumps(json_obj, ensure_ascii=False, indent=2)
            ext = "json"
        else:
            lines = [f"对话 ID: {cid}"]
            if conv.title:
                lines.append(f"标题: {conv.title}")
            lines.append(f"消息总数: {len(history)}")
            lines.append("=" * 40)
            lines.append("")

            for i, msg in enumerate(history, 1):
                role = msg.get("role", "unknown")
                msg_content = msg.get("content", "")
                lines.append(f"[{i}] {role.upper()}")
                lines.append(str(msg_content))
                lines.append("")

            content = "\n".join(lines)
            ext = "txt"

        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"context_{cid[:8]}_{int(time.time())}.{ext}")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)

        async for result in self._send_file(event, "上下文", tmp_path, len(history)):
            yield result

    @filter.command("viewprompt")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def viewprompt(self, event: AstrMessageEvent):
        """查看当前对话使用的提示词并导出为文件（仅管理员）"""
        allowed, msg = self._check_permission(event)
        if not allowed:
            yield event.plain_result(msg)
            return
        umo = event.unified_msg_origin
        conv_mgr = self.context.conversation_manager
        persona_mgr = self.context.persona_manager

        cid = await conv_mgr.get_curr_conversation_id(umo)
        if not cid:
            yield event.plain_result("当前没有活跃的对话。")
            return

        conv = await conv_mgr.get_conversation(umo, cid)

        persona_id = conv.persona_id if conv and conv.persona_id else None
        if persona_id:
            persona = persona_mgr.get_persona_v3_by_id(persona_id)
        else:
            persona = await persona_mgr.get_default_persona_v3(umo)

        if not persona:
            yield event.plain_result("未找到当前对话使用的提示词。")
            return

        output_format = self.config.get("output_format", "text")

        if output_format == "json":
            json_obj = {
                "persona_name": persona["name"],
                "prompt": persona["prompt"],
                "begin_dialogs": persona.get("begin_dialogs", []),
                "tools": persona.get("tools"),
                "skills": persona.get("skills"),
                "custom_error_message": persona.get("custom_error_message"),
            }
            content = json.dumps(json_obj, ensure_ascii=False, indent=2)
            ext = "json"
        else:
            lines = [f"人格名称: {persona['name']}"]
            lines.append("=" * 40)
            lines.append("")
            lines.append(persona["prompt"])
            lines.append("")

            begin_dialogs = persona.get("begin_dialogs", [])
            if begin_dialogs:
                lines.append("=" * 40)
                lines.append("预设对话 (Begin Dialogs):")
                lines.append("=" * 40)
                for dialog in begin_dialogs:
                    lines.append(str(dialog))
                    lines.append("")

            tools = persona.get("tools")
            if tools is not None:
                lines.append(f"工具权限: {tools}")
            skills = persona.get("skills")
            if skills is not None:
                lines.append(f"技能权限: {skills}")
            custom_error = persona.get("custom_error_message")
            if custom_error:
                lines.append(f"自定义错误消息: {custom_error}")

            content = "\n".join(lines)
            ext = "txt"

        tmp_dir = tempfile.gettempdir()
        safe_name = persona["name"].replace(" ", "_")[:16]
        tmp_path = os.path.join(tmp_dir, f"prompt_{safe_name}_{int(time.time())}.{ext}")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)

        async for result in self._send_file(event, "提示词", tmp_path, 1):
            yield result

    async def terminate(self):
        pass
