import json
import os
import subprocess
import sys
from pathlib import Path


def _env_with_src() -> dict:
    env = os.environ.copy()
    # Ensure repository src is on PYTHONPATH
    repo_root = Path(__file__).resolve().parents[2]
    src_path = str(repo_root / "src")
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{current}" if current else src_path
    return env


def test_fertilize_recommend_help_shows(parser_output_capture=None):
    cmd = [sys.executable, "-m", "agrr_core.cli", "fertilize", "recommend", "--help"]
    result = subprocess.run(cmd, env=_env_with_src(), capture_output=True, text=True)
    assert result.returncode == 0
    out = (result.stdout or "") + (result.stderr or "")
    assert "Recommend fertilizer plan (N,P,K in g/m2)" in out
    assert "--crop-file" in out


def test_fertilize_recommend_executes_with_sample_crop(tmp_path):
    # Minimal valid crop profile
    crop_profile = {
        "crop": {
            "crop_id": "tomato",
            "name": "Tomato",
            "area_per_unit": 1.0,
        },
        "stage_requirements": [],
    }
    crop_file = tmp_path / "tomato_profile.json"
    crop_file.write_text(json.dumps(crop_profile), encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "agrr_core.cli",
        "fertilize",
        "recommend",
        "--crop-file",
        str(crop_file),
        "--json",
    ]
    result = subprocess.run(cmd, env=_env_with_src(), capture_output=True, text=True)
    assert result.returncode == 0
    # Expect JSON on stdout
    assert result.stdout.strip() != ""
    data = json.loads(result.stdout)
    # Basic shape checks
    assert "totals" in data
    assert "applications" in data
    assert isinstance(data["applications"], list) and len(data["applications"]) >= 1
    for key in ("N", "P", "K"):
        assert key in data["totals"]


