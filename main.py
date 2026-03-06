"""
架构入口：启动 FastAPI 服务，baseUrl 为 http://ip:port/{type}/v1/...
示例：http://127.0.0.1:8000/claude/v1/chat/completions
"""

# 尽早设置，让 Chromium 派生的 Node 子进程继承，抑制 url.parse 等 DeprecationWarning
import os
import logging
import sys
import uvicorn

from core.config.settings import apply_env_from_config

# 先从 config.yaml 中加载配置并写入环境变量（如 CLAUDE_START_URL / CLAUDE_API_BASE）
apply_env_from_config()

_opt = os.environ.get("NODE_OPTIONS", "").strip()
if "--no-deprecation" not in _opt:
    os.environ["NODE_OPTIONS"] = (_opt + " --no-deprecation").strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> int:
    uvicorn.run(
        "core.app:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
