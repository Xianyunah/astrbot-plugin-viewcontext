# astrbot-plugin-viewcontext

一个 AstrBot 插件，用于查看和导出当前 LLM 对话上下文及提示词。

## 指令

| 指令 | 权限 | 说明 |
|---|---|---|
| `/viewcontext` | 管理员 | 导出当前对话的所有历史消息 |
| `/viewprompt` | 管理员 | 导出当前对话使用的系统提示词（Persona） |

## 功能

- 获取当前对话的所有历史消息（User / Assistant 角色）
- 获取当前对话使用的系统提示词（含预设对话、工具权限等）
- 支持导出为可读文本格式 (`.txt`) 或原始 JSON 格式 (`.json`)
- 可通过配置将文件自动发送给指定用户（私聊）

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `target_user_id` | string | `""` | 指定接收文件的用户 ID（留空则发给命令调用者） |
| `output_format` | string | `"text"` | 导出文件格式，可选 `text`（可读文本）或 `json`（原始 JSON） |

### 配置示例

在 AstrBot 插件管理页面中设置或在 `data/config/viewcontext_plugin_config.json` 中手动编辑：

```json
{
  "target_user_id": "123456789",
  "output_format": "json"
}
```

## 链接

- [AstrBot Repo](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot 插件开发文档](https://docs.astrbot.app/dev/star/plugin-new.html)
