# SPDX-License-Identifier: MIT-0
"""Static repository controls that must not regress silently."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_workflow_actions_are_sha_pinned_and_pr_safe() -> None:
    action_reference = re.compile(r"^\s*- uses:\s+[^@\s]+@([^\s#]+)", re.MULTILINE)
    full_sha = re.compile(r"^[0-9a-f]{40}$")
    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        content = workflow.read_text(encoding="utf-8")
        references = action_reference.findall(content)
        assert references, f"{workflow.name} must contain auditable action references"
        assert all(full_sha.fullmatch(reference) for reference in references), workflow.name
        assert "pull_request_target" not in content
        assert re.search(r"^permissions:", content, re.MULTILINE), workflow.name


def test_terraform_does_not_enable_excluded_services_or_build_during_apply() -> None:
    terraform = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / "terraform").glob("*.tf"))
    )
    resource_types = set(re.findall(r'^resource\s+"([^"]+)"', terraform, re.MULTILINE))
    forbidden = {
        "aws_guardduty_detector",
        "aws_inspector2_enabler",
        "aws_macie2_account",
        "aws_config_configuration_recorder",
        "aws_organizations_organization",
    }
    assert resource_types.isdisjoint(forbidden)
    assert not any(resource_type.startswith("aws_securityhub_") for resource_type in resource_types)
    assert "local-exec" not in terraform


def test_release_version_and_clone_url_are_consistent() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["version"] == "0.1.0"
    runtime_pins = {
        line.split("==", maxsplit=1)[0]: line
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if "==" in line and not line.startswith("#")
    }
    for dependency in metadata["project"]["dependencies"]:
        name = dependency.split("==", maxsplit=1)[0]
        assert runtime_pins[name] == dependency
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "github.com/Sebasarabia/aws-security-hub-workflow.git" in readme
    assert "github.com/OWNER/" not in readme
