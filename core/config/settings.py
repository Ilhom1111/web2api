"""
统一的 YAML 配置加载与环境变量适配。

目前主要用于替代 .env：
- claude.start_url / claude.api_base -> CLAUDE_START_URL / CLAUDE_API_BASE
- mock.port -> MOCK_PORT
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"


def load_config() -> dict[str, Any]:
    """加载根目录下的 config.yaml，不存在时返回空 dict。"""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}
        return dict(data)
    except Exception:
        # 配置异常时不阻塞服务启动，回退到默认值/环境变量
        return {}


def apply_env_from_config(config: Mapping[str, Any] | None = None) -> None:
    """
    根据 YAML 配置写入进程环境变量，为现有代码提供兼容：
    - CLAUDE_START_URL / CLAUDE_API_BASE
    - MOCK_PORT
    已存在的环境变量优先，不会被 YAML 覆盖。
    """
    if config is None:
        config = load_config()

    # Claude 相关 URL
    claude_cfg = config.get("claude") or {}
    if isinstance(claude_cfg, Mapping):
        start_url = claude_cfg.get("start_url")
        api_base = claude_cfg.get("api_base")
        if start_url and not os.environ.get("CLAUDE_START_URL"):
            os.environ["CLAUDE_START_URL"] = str(start_url)
        if api_base and not os.environ.get("CLAUDE_API_BASE"):
            os.environ["CLAUDE_API_BASE"] = str(api_base)

    # Mock 服务端口
    mock_cfg = config.get("mock") or {}
    if isinstance(mock_cfg, Mapping):
        port = mock_cfg.get("port")
        if port is not None and not os.environ.get("MOCK_PORT"):
            os.environ["MOCK_PORT"] = str(port)
