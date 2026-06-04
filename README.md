# astrbot-plugin-viewcontext

一个 AstrBot 插件，用于查看和导出当前 LLM 对话上下文内容。

## 功能

- 输入 `/viewcontext` 指令（仅管理员可用）
- 获取当前对话的所有历史消息（User / Assistant 角色）
- 格式化为可读文本并导出为 `.txt` 文件
- 可通过配置将文件自动发送给指定用户（私聊）

## 配置

在插件配置中设置 `target_user_id`，填入目标用户的平台 ID（如 QQ 号）：

- 留空：文件发送给命令调用者
- 填写：文件通过私聊发送给该用户
