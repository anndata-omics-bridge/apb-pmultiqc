"""The development installation uses the same immutable sources as the application lock."""

from __future__ import annotations

import json
import re
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_installed_git_sources_match_all_declared_revisions() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies: list[str] = project["project"]["dependencies"]
    pinned = [entry for entry in dependencies if " @ git+" in entry]
    assert len(pinned) == 7
    assert project["tool"]["uv"]["no-sources"] is True
    assert "sources" not in project["tool"]["uv"]
    for entry in pinned:
        name, source = entry.split(" @ ")
        revision = source.rsplit("@", 1)[1]
        assert re.fullmatch(r"[0-9a-f]{40}", revision), entry
        direct = metadata.distribution(name).read_text("direct_url.json")
        assert direct is not None
        installed = json.loads(direct)
        assert installed["vcs_info"]["commit_id"] == revision
        assert installed["url"] == source.removeprefix("git+").rsplit("@", 1)[0]
        assert "dir_info" not in installed
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    for package in lock["package"]:
        source = package["source"]
        assert "path" not in source and "directory" not in source
        if package["name"] != "apb-pmultiqc":
            assert "editable" not in source


def test_one_distribution_owns_the_executable() -> None:
    owners = [
        distribution.metadata["Name"]
        for distribution in metadata.distributions()
        if any(
            entry.name == "apb-pmultiqc" and entry.group == "console_scripts"
            for entry in distribution.entry_points
        )
    ]
    assert owners == ["apb-pmultiqc"]
