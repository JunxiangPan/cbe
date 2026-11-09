"""F5/F6 release-train component status and body fragments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import InputError
from .jsonio import load_json

from .paths import schema_path

RELEASE_TRAIN_SCHEMA = schema_path("v1.7", "release-train.schema.json")
COMPONENTS = ("cbm", "cbc")
NOT_UPLOADED = "NOT_UPLOADED"
EVIDENCE_ABSENT = "EVIDENCE_ABSENT"
SKIPPED_INFRA = "SKIPPED_INFRA"
PASS = "PASS"
PRECONDITION_FAIL = "PRECONDITION_FAIL"


@dataclass
class Component:
    name: str
    declared_attached: bool
    status: str
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "declared_attached": self.declared_attached,
            "status": self.status,
            "reason": self.reason,
        }


def load_release_train(path: str | Path) -> dict[str, Any]:
    data = load_json(path)
    try:
        schema = json.loads(RELEASE_TRAIN_SCHEMA.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError("RELEASE_TRAIN_SCHEMA_UNAVAILABLE", f"cannot read release-train schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        raise InputError("RELEASE_TRAIN_INVALID", f"release-train is invalid: {errors[0].message}")
    return data


def components(data: dict[str, Any]) -> list[Component]:
    result: list[Component] = []
    for name in COMPONENTS:
        item = data["components"][name]
        result.append(
            Component(
                name=name,
                declared_attached=bool(item["declared_attached"]),
                status=str(item["status"]),
                reason=str(item.get("reason", "")),
            )
        )
    return result


def classify(components_: list[Component]) -> tuple[list[str], list[str], list[str]]:
    not_uploaded = [item.name for item in components_ if item.status == NOT_UPLOADED]
    evidence_absent = [item.name for item in components_ if item.status == EVIDENCE_ABSENT]
    infra = [item.name for item in components_ if item.status == SKIPPED_INFRA]
    return not_uploaded, evidence_absent, infra


def body_section(components_: list[Component]) -> str:
    not_uploaded, evidence_absent, infra = classify(components_)
    lines: list[str] = []
    if infra:
        lines += ["## Infrastructure failures", ""]
        lines += [f"- {name}: SKIPPED_INFRA" for name in infra]
        lines.append("")
    lines += ["## NOT_UPLOADED", ""]
    if not_uploaded:
        for name in not_uploaded:
            component = next(item for item in components_ if item.name == name)
            if component.declared_attached:
                lines.append(f"- {name}: NOT_UPLOADED — declared as attached but not uploaded")
            else:
                lines.append(f"- {name}: NOT_UPLOADED")
    if evidence_absent:
        lines += [f"- {name}: EVIDENCE_ABSENT" for name in evidence_absent]
    if not not_uploaded and not evidence_absent:
        lines.append("- none")
    lines.append("")
    lines.append("NOT_UPLOADED is not PASS, not SKIP, and is not counted in any denominator.")
    return "\n".join(lines) + "\n"


def status(components_: list[Component]) -> tuple[int, str]:
    if any(item.status == SKIPPED_INFRA for item in components_):
        return 3, SKIPPED_INFRA
    if any(item.status == PRECONDITION_FAIL for item in components_):
        return 3, PRECONDITION_FAIL
    return 0, PASS
