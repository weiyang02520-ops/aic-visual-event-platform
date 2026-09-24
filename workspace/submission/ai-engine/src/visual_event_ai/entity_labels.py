"""Shared semantic labels used to route detections into person/object logic."""

from collections.abc import Mapping
import re
from typing import Any


_PERSON_LABELS = frozenset({"person", "人", "老人", "家属", "worker", "工作人员", "staff"})
_MEDICATION_WORDS = frozenset({"drug", "medicine", "medication", "pill", "pills", "tablet", "tablets", "capsule", "capsules"})
_MEDICATION_STORAGE_LABELS = (
    "药品柜",
    "储药柜",
    "医药柜",
    "药柜",
    "药品架",
    "药架",
    "药房",
    "药品仓库",
    "medicine cabinet",
    "medication cabinet",
    "drug cabinet",
    "medicine shelf",
    "medication shelf",
    "medicine storage",
    "medication storage",
    "pharmacy",
    "dispensary",
    "drugstore",
)
_MEDICATION_DOCUMENT_LABELS = (
    "药品说明书",
    "药物说明书",
    "用药说明",
    "药品清单",
    "药品目录",
    "用药记录",
    "处方单",
    "处方笺",
    "medication list",
    "medicine instructions",
    "package insert",
    "prescription form",
)


def is_person_label(label: object) -> bool:
    """Classify supported person labels independent of ASCII casing/spacing."""

    return str(label or "").strip().casefold() in _PERSON_LABELS


def is_person_entity(entity: Mapping[str, Any] | None) -> bool:
    if not isinstance(entity, Mapping):
        return False
    return is_person_label(entity.get("label"))


def is_medication_entity(entity: Mapping[str, Any] | None) -> bool:
    if not isinstance(entity, Mapping):
        return False
    label = str(entity.get("label", "")).strip().casefold()
    category = str(entity.get("category", "")).strip().casefold()
    if category in {"medicine", "medication", "drug"}:
        return True
    if any(storage_label in label for storage_label in _MEDICATION_STORAGE_LABELS):
        return False
    if any(document_label in label for document_label in _MEDICATION_DOCUMENT_LABELS):
        return False
    if "药" in label:
        return True
    return bool(set(re.findall(r"[a-z]+", label)) & _MEDICATION_WORDS)
