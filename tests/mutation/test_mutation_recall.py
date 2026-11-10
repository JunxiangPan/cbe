"""Mutation recall gate for enforce-no-bypass."""

from __future__ import annotations

from run_mutations import run_mutations


def test_mutation_recall_at_least_95_percent() -> None:
    report = run_mutations()
    assert report["total"] >= 10
    assert report["recall"] >= 0.95, report
    assert all(item["matched"] for item in report["results"]), report
    assert all(item["gate_status"] != "PASS" for item in report["results"])
