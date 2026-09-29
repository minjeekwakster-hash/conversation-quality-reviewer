"""ABCD dataset loading and parsing."""

from __future__ import annotations

import gzip
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .models import (
    Conversation,
    DelexedTurn,
    OrderInfo,
    PersonalInfo,
    ProductInfo,
    Scenario,
    Speaker,
    Turn,
)

DATA_DIR = Path(__file__).parent.parent / "data"


def _parse_turn(raw: list) -> Turn:
    return Turn(speaker=Speaker(raw[0]), text=raw[1])


def _parse_delexed_turn(raw: dict) -> DelexedTurn:
    return DelexedTurn(
        speaker=Speaker(raw["speaker"]),
        text=raw["text"],
        turn_count=raw["turn_count"],
        targets=raw.get("targets", []),
        candidates=raw.get("candidates", []),
    )


def _parse_scenario(raw: dict) -> Scenario:
    personal = PersonalInfo(**raw.get("personal", {}))
    order = OrderInfo(**raw.get("order", {}))
    prod = raw.get("product", {})
    product = ProductInfo(
        names=prod.get("names", []),
        amounts=[float(a) for a in prod.get("amounts", [])],
    )
    return Scenario(
        personal=personal,
        order=order,
        product=product,
        flow=raw.get("flow", ""),
        subflow=raw.get("subflow", ""),
    )


def parse_conversation(raw: dict) -> Conversation:
    """Parse a single raw conversation dict into a Conversation model."""
    return Conversation(
        convo_id=raw["convo_id"],
        scenario=_parse_scenario(raw.get("scenario", {})),
        original=[_parse_turn(t) for t in raw.get("original", [])],
        delexed=[_parse_delexed_turn(t) for t in raw.get("delexed", [])],
    )


def load_dataset(
    split: str = "train",
    data_dir: Optional[Path] = None,
) -> list[Conversation]:
    """Load conversations from the ABCD dataset.

    Tries abcd_v1.1.json.gz first, then abcd_v1.1.json.
    """
    data_dir = data_dir or DATA_DIR

    gz_path = data_dir / "abcd_v1.1.json.gz"
    json_path = data_dir / "abcd_v1.1.json"

    if gz_path.exists():
        with gzip.open(gz_path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    elif json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        raise FileNotFoundError(
            f"ABCD dataset not found in {data_dir}. "
            "Run `python scripts/download_data.py` first."
        )

    raw_convos = data.get(split, [])
    return [parse_conversation(c) for c in raw_convos]


def load_sample(data_dir: Optional[Path] = None) -> list[Conversation]:
    """Load the small sample file (abcd_sample.json) for testing."""
    data_dir = data_dir or DATA_DIR
    sample_path = data_dir / "abcd_sample.json"
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found at {sample_path}")
    with open(sample_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Sample file is {"train": [...]}
    convos = raw.get("train", raw) if isinstance(raw, dict) else raw
    return [parse_conversation(c) for c in convos]


def load_kb(data_dir: Optional[Path] = None) -> dict[str, list[str]]:
    """Load kb.json — maps subflow -> expected action sequence."""
    data_dir = data_dir or DATA_DIR
    kb_path = data_dir / "kb.json"
    if not kb_path.exists():
        raise FileNotFoundError(f"kb.json not found at {kb_path}")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_guidelines(data_dir: Optional[Path] = None) -> dict:
    """Load guidelines.json — human-readable procedural rules."""
    data_dir = data_dir or DATA_DIR
    gpath = data_dir / "guidelines.json"
    if not gpath.exists():
        raise FileNotFoundError(f"guidelines.json not found at {gpath}")
    with open(gpath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_ontology(data_dir: Optional[Path] = None) -> dict:
    """Load ontology.json — flow/subflow/action taxonomy."""
    data_dir = data_dir or DATA_DIR
    opath = data_dir / "ontology.json"
    if not opath.exists():
        raise FileNotFoundError(f"ontology.json not found at {opath}")
    with open(opath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_precomputed(data_dir: Optional[Path] = None) -> list[dict]:
    """Load pre-computed scores from JSON."""
    data_dir = data_dir or DATA_DIR
    path = data_dir / "precomputed_scores.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def stratified_sample(
    conversations: list[Conversation],
    per_flow: int = 20,
    seed: int = 42,
) -> list[Conversation]:
    """Select a stratified sample with ~per_flow conversations per flow."""
    by_flow: dict[str, list[Conversation]] = defaultdict(list)
    for c in conversations:
        by_flow[c.scenario.flow].append(c)

    rng = random.Random(seed)
    sampled = []
    for flow, convos in sorted(by_flow.items()):
        k = min(per_flow, len(convos))
        sampled.extend(rng.sample(convos, k))

    return sampled
