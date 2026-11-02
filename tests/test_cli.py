"""CLI wiring: parsing, config precedence and entry points."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import cellatlas
from cellatlas.cli.main import build_config, build_parser, main

ROOT = Path(__file__).resolve().parents[1]


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert cellatlas.__version__ in capsys.readouterr().out


def test_cli_flags_override_config_file(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"resolutions": [0.3], "random_state": 7}))
    args = build_parser().parse_args(
        ["cluster", "--config", str(cfg), "--seed", "42", "--data-dir", str(tmp_path)]
    )
    config = build_config(args)
    assert config.resolutions == [0.3]       # from file
    assert config.random_state == 42         # CLI wins over file
    assert config.data_dir == tmp_path


def test_unknown_config_key_is_rejected(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"resolutionz": [0.3]}))
    assert main(["cluster", "--config", str(cfg)]) == 1


def test_missing_input_returns_error_code(tmp_path, capsys):
    code = main(["annotate", "--data-dir", str(tmp_path),
                 "--figures-dir", str(tmp_path), "--results-dir", str(tmp_path)])
    assert code == 1
    assert "cellatlas cluster" in capsys.readouterr().err


@pytest.mark.parametrize(
    "cmd",
    [
        [sys.executable, "main.py", "--version"],
        [sys.executable, "-m", "cellatlas", "--version"],
        [sys.executable, str(Path("src") / "cellatlas"), "--version"],
    ],
)
def test_entry_points(cmd):
    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    assert out.returncode == 0, out.stderr
    assert cellatlas.__version__ in out.stdout
