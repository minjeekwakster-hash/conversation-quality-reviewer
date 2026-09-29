"""Pre-compute quality scores for demo conversations.

Runs efficiency (heuristic) on all conversations, then full LLM scoring on a
stratified sample of ~200 conversations. Saves results incrementally.

Usage:
    python scripts/seed_data.py                    # Full run (~200 LLM-scored)
    python scripts/seed_data.py --sample-size 20   # Quick test run
    python scripts/seed_data.py --heuristic-only   # Heuristic scoring only (no API key needed)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.ingest import load_dataset, load_kb, stratified_sample
from src.models import ConversationResult
from src.signals.efficiency import EfficiencySignal
from src.engine import ScoringEngine

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "precomputed_scores.json"


def save_results(results: list[ConversationResult]):
    """Save results to JSON, preserving any existing results."""
    existing = {}
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r") as f:
            for raw in json.load(f):
                existing[raw["convo_id"]] = raw

    # Merge new results
    for r in results:
        existing[r.convo_id] = r.model_dump()

    with open(OUTPUT_PATH, "w") as f:
        json.dump(list(existing.values()), f, indent=2, default=str)

    print(f"Saved {len(existing)} total results to {OUTPUT_PATH}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=20,
                        help="Conversations per flow for LLM scoring")
    parser.add_argument("--heuristic-only", action="store_true",
                        help="Only run heuristic scoring (no API key needed)")
    args = parser.parse_args()

    print("Loading ABCD dataset...")
    try:
        conversations = load_dataset("train")
    except FileNotFoundError:
        print("ERROR: Dataset not found. Run `python scripts/download_data.py` first.")
        sys.exit(1)

    print(f"Loaded {len(conversations)} conversations")

    # Load knowledge base for compliance
    try:
        kb = load_kb()
    except FileNotFoundError:
        kb = {}
        print("WARNING: kb.json not found — compliance scoring will be limited")

    # Step 1: Compute per-subflow baselines
    print("\nComputing per-subflow baselines...")
    baselines = EfficiencySignal.compute_baselines(conversations)
    print(f"Baselines computed for {len(baselines)} subflows")

    # Step 2: Heuristic scoring on ALL conversations
    print(f"\nScoring all {len(conversations)} conversations (heuristic only)...")
    heuristic_engine = ScoringEngine(
        anthropic_client=None,
        baselines=baselines,
        kb=kb,
        llm_enabled=False,
    )

    heuristic_results = []
    start = time.time()
    for i, convo in enumerate(conversations):
        result = await heuristic_engine.score_conversation(convo, use_cache=False)
        heuristic_results.append(result)
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start
            print(f"  {i+1}/{len(conversations)} ({elapsed:.1f}s)")

    elapsed = time.time() - start
    print(f"Heuristic scoring complete: {len(heuristic_results)} conversations in {elapsed:.1f}s")
    save_results(heuristic_results)

    if args.heuristic_only:
        print("\n--heuristic-only flag set. Skipping LLM scoring.")
        return

    # Step 3: LLM scoring on stratified sample
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nNo ANTHROPIC_API_KEY set. Skipping LLM scoring.")
        print("Set the key in .env and re-run to add LLM-based scores.")
        return

    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key)

    sample = stratified_sample(conversations, per_flow=args.sample_size)
    print(f"\nLLM scoring {len(sample)} conversations (stratified sample, {args.sample_size}/flow)...")

    llm_engine = ScoringEngine(
        anthropic_client=client,
        baselines=baselines,
        kb=kb,
        llm_enabled=True,
        max_concurrent=5,
    )

    llm_results = []
    start = time.time()
    for i, convo in enumerate(sample):
        try:
            result = await llm_engine.score_conversation(convo, use_cache=False)
            llm_results.append(result)
        except Exception as e:
            print(f"  ERROR scoring convo {convo.convo_id}: {e}")

        if (i + 1) % 10 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = (len(sample) - i - 1) / rate
            print(f"  {i+1}/{len(sample)} ({elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining)")
            # Save incrementally
            save_results(heuristic_results + llm_results)

    # Final save
    save_results(heuristic_results + llm_results)
    elapsed = time.time() - start
    print(f"\nLLM scoring complete: {len(llm_results)} conversations in {elapsed:.0f}s")
    print(f"Total scored: {len(heuristic_results)} heuristic + {len(llm_results)} full LLM")


if __name__ == "__main__":
    asyncio.run(main())
