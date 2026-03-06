# Web2API

一个基于 **FastAPI + Playwright + CDP** 的“Web2API”服务：通过**真实浏览器会话**访问站点，并以 **OpenAI 兼容**的接口形式对外提供 `/{type}/v1/chat/completions` 能力（按 `type` 插件化路由，例如 `claude`）。

> 适用场景：你已经有 OpenAI SDK / Cursor / 其它兼容 `/v1/chat/completions` 的客户端，希望把“网页端能力”以统一接口接入，并支持会话复用、工具调用（tool calls）等编排。

## 功能特性

- **OpenAI 兼容接口**：`GET /{type}/v1/models`、`POST /{type}/v1/chat/completions`（支持 `stream`）。
- **插件化**：通过 `core.plugin.base.AbstractPlugin` 扩展新的 `type`（同一套 API，不同实现；目前只实现了 claude 插件）。
- **配置页 + 配置 API**：浏览器访问 `/config` 维护代理组与账号；或通过 `GET/PUT /api/config` 管理。
- **会话复用**：大大加快响应速度。
- **ReAct → tool_calls**：当请求里携带 `tools` 时，会把 ReAct 格式输出解析成 OpenAI `tool_calls`（便于 Cursor 等客户端执行工具）。
- **Mock 服务**：`main_mock.py` 提供调试用 “Mock Claude API”，不消耗 token，便于联调 SSE/解析逻辑。

## 依赖与环境

- Python：**3.12+**
- 包管理/运行：推荐使用 [`uv`](https://github.com/astral-sh/uv)
- 安装：[指纹浏览器](https://github.com/adryfish/fingerprint-chromium)
- 安装虚拟屏幕（**仅 Linux / 无桌面环境服务器需要，可选**）：
  - Ubuntu/Debian：`sudo apt update && sudo apt install -y xvfb`
  - 使用虚拟屏幕启动服务示例：`xvfb-run -s "-screen 0 1920x1080x24" uv run python main.py`

## 快速开始

### 1）安装依赖

```bash
uv sync
```

### 2）启动服务

```bash
uv run python main.py
```

默认监听：`http://127.0.0.1:8001`

- 配置页：`GET http://127.0.0.1:8001/config`
- Types 列表：`GET http://127.0.0.1:8001/api/types`

> 服务启动后如果提示“ 数据库无配置”，先去 `/config` 添加配置，或调用 `PUT /api/config` 写入。

### 配置存储 `db.sqlite3`

项目使用根目录下的 SQLite：`db.sqlite3` 保存配置（代理组 + 账号）。该文件通常包含敏感信息（代理密码、sessionKey），**不建议提交到公开仓库**。

配置结构（与 `/api/config` 一致）：

```json
[
  {
    "proxy_host": "host:port",
    "proxy_user": "user",
    "proxy_pass": "pass",
    "fingerprint_id": "4567",
    "timezone": "America/Chicago",
    "accounts": [
      {
        "name": "claude-01",
        "type": "claude",
        "auth": { "sessionKey": "YOUR_SESSION_KEY" }
      }
    ]
  }
]
```

说明：

- `fingerprint_id`：用于隔离/复用浏览器上下文（指纹/用户数据目录等会按它组织）。
- `accounts[].type`：必须是已注册的插件类型（可从 `/api/types` 获取）。
- `accounts[].auth`：各插件自定义；Claude 插件需要 `sessionKey` 或 `session_key`。

## API 使用示例

以下以 `type=claude` 为例（baseUrl 为 `http://127.0.0.1:8001/claude`）。

### 列出模型

```bash
curl "http://127.0.0.1:8001/claude/v1/models"
```

### 非流式 Chat Completions

```bash
curl -s "http://127.0.0.1:8001/claude/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "s4",
    "stream": false,
    "messages": [
      {"role":"user","content":"你好，简单介绍一下你自己。"}
    ]
  }'
```

### 流式（SSE）

```bash
curl -N "http://127.0.0.1:8001/claude/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "s4",
    "stream": true,
    "messages": [
      {"role":"user","content":"用三点总结今天的计划。"}
    ]
  }'
```

## Mock 调试（可选）

启动 mock 服务：

```bash
uv run python main_mock.py
```

默认端口：`8002`，并提供：

- `GET http://127.0.0.1:8002/mock`（模拟站点入口页）
- 一组与 Claude 插件调用格式兼容的 mock 接口（用于联调 SSE、解析器、工具调用等逻辑）

让主服务指向 mock：

- 在 `config.yaml` 中设置：
  - `claude.start_url: "http://127.0.0.1:8002/mock"`
  - `claude.api_base: "http://127.0.0.1:8002/mock"`

然后再启动 `main.py`。

> mock completion 请求到达时会在终端提示你输入多行“要回复的内容”，空行结束输入。

## 扩展新的 type（插件开发）

1. 实现 `core.plugin.base.AbstractPlugin`（关注：`create_page` / `apply_auth` / `create_conversation` / `stream_completion` 等）。
2. 在应用启动时注册插件（参考 `core.plugin.claude.register_claude_plugin()`）。
3. 在配置中为该 `type` 添加账号，然后即可通过 `/{your_type}/v1/chat/completions` 调用。

更细的架构说明见：`core/README.md`。

## 项目结构（简述）

- `main.py`：启动 FastAPI 主服务（默认 `8001`）
- `main_mock.py`：启动 Mock 服务（默认 `8002`）
- `core/app.py`：应用组装（配置、账号池、会话缓存、浏览器管理、插件注册、路由挂载）
- `core/api/`：OpenAI 兼容路由、ReAct/tool_calls 解析与 SSE 输出
- `core/config/`：配置模型与 SQLite 持久化（`db.sqlite3`）
- `core/plugin/`：插件接口与实现（默认含 Claude）
- `core/runtime/`：浏览器/CDP/page 池、session 缓存等运行时组件

## 开发与质量

```bash
uv run ruff check .
```

（如需格式化/更多检查，可在此基础上扩展 ruff 配置。）

## 安全与合规提示

- **不要把敏感信息提交到公开仓库**：如 `db.sqlite3`、代理账号密码、站点 `sessionKey`、抓包数据等。
- 该项目通过真实浏览器访问第三方站点/接口，请确保你拥有合法使用权限，并遵守对应站点的条款与当地法律法规。
