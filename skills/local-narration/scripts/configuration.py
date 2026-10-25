"""Resolve a private narration configuration without importing audio runtimes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

SKILL = Path(__file__).resolve().parents[1]
ENVIRONMENT_TOKEN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)|%([A-Za-z_][A-Za-z0-9_]*)%")


def expand_path(value, base):
    """Resolve environment variables, home, and config-relative paths."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Configured paths must be nonempty strings.")

    def replace(match):
        name = next(group for group in match.groups() if group is not None)
        if name not in os.environ or not os.environ[name]:
            raise ValueError(f"Environment variable {name} is unset; configure a path or set the variable.")
        return os.environ[name]

    path = Path(ENVIRONMENT_TOKEN.sub(replace, value)).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def load_config(selected=None):
    """Read explicit, environment-selected, or installed private configuration."""
    value = str(selected) if selected is not None else os.environ.get("LOCAL_NARRATION_CONFIG")
    config_path = expand_path(value, Path.cwd()) if value else SKILL / "config/local.json"
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration missing: {config_path}. Copy config/example.json to config/local.json, "
            "set existing resource paths, or pass --config."
        )
    cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    for field in ("python", "ffmpeg"):
        cfg[field] = str(expand_path(cfg[field], base))
    cfg["reference"]["audio"] = str(expand_path(cfg["reference"]["audio"], base))
    for spec in cfg["engines"].values():
        for field in ("repository", "model"):
            spec[field] = str(expand_path(spec[field], base))
        for field, value in spec.get("aux_paths", {}).items():
            spec["aux_paths"][field] = str(expand_path(value, base))
    cfg["subtitles"]["asr_cache"] = str(expand_path(cfg["subtitles"]["asr_cache"], base))
    return cfg, config_path
