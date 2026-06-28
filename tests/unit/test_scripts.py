"""示例配置运行脚本的静态契约测试。"""

from __future__ import annotations

from pathlib import Path

import yaml

MAP_PATH = Path("scripts/script_config_map.yaml")


def _load_script_map() -> dict:
    raw = yaml.safe_load(MAP_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _entries() -> list[dict]:
    mapping = _load_script_map()
    entries: list[dict] = []
    for group_name, group in mapping["groups"].items():
        for entry in group["entries"]:
            entries.append({**entry, "group": group_name, "group_data": group})
    return entries


def test_every_example_config_is_mapped_to_one_classified_script() -> None:
    config_paths = sorted(str(path) for path in Path("configs").rglob("*.yaml"))
    scripted_configs = sorted(entry["config"] for entry in _entries())

    assert scripted_configs == config_paths
    assert all("tourism_small" not in config for config in scripted_configs)


def test_script_map_classifies_by_config_directory() -> None:
    for entry in _entries():
        group = entry["group"]
        config = Path(entry["config"])
        script = Path(entry["script"])

        assert entry["group_data"]["config_dir"] == str(config.parent)
        assert entry["group_data"]["scripts_dir"] == str(script.parent)
        assert config.parent.name == group
        assert script.parent.name == group


def test_scripts_use_uv_run_cli_without_uv_cache() -> None:
    for entry in _entries():
        script = Path(entry["script"])
        text = script.read_text()

        assert 'cd "$ROOT_DIR"' in text
        assert "exec uv run python -m tsforecasting.main_cli" in text
        assert ".venv/bin/tsforecasting" not in text
        assert ".uv_cache" not in text
        assert "UV_CACHE_DIR" not in text
        assert f'"{entry["command"]}"' in text
        assert entry["config"] in text
        assert '"$@"' in text


def test_script_map_contains_only_forecast_commands() -> None:
    assert {entry["command"] for entry in _entries()} == {"run"}
