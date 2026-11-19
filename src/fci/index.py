"""Facility Condition Index: deferred maintenance cost divided by replacement value."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Commonly quoted bands. Organizations set their own; pass others to rate().
DEFAULT_BANDS: tuple[tuple[float, str], ...] = ((0.05, "Good"), (0.10, "Fair"), (0.30, "Poor"))
WORST_RATING = "Critical"


@dataclass(frozen=True)
class BuildingResult:
    """FCI result for one building."""

    building: str
    deferred_maintenance: float
    replacement_value: float
    fci: float
    rating: str
    worst_system: str


def rate(fci: float, bands: tuple[tuple[float, str], ...] = DEFAULT_BANDS) -> str:
    """Rating for an FCI value. A value equal to a band limit takes that band."""
    for limit, label in bands:
        if fci <= limit:
            return label
    return WORST_RATING


def compute_fci(deferred_maintenance: float, replacement_value: float) -> float:
    """FCI as a ratio. Raises ValueError for a zero or negative replacement value."""
    if replacement_value <= 0:
        raise ValueError("replacement value must be positive")
    if deferred_maintenance < 0:
        raise ValueError("deferred maintenance cannot be negative")
    return deferred_maintenance / replacement_value


def read_systems(path: str | Path) -> list[dict]:
    """Read system rows: building, system, repair_cost, replacement_value."""
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=1):
            try:
                rows.append({
                    "building": row["building"].strip(),
                    "system": row["system"].strip(),
                    "repair_cost": float(row["repair_cost"]),
                    "replacement_value": float(row["replacement_value"]),
                })
            except (KeyError, ValueError, AttributeError) as error:
                raise ValueError(f"row {number}: {error!r}") from error
    return rows


def analyze(rows: list[dict], bands: tuple[tuple[float, str], ...] = DEFAULT_BANDS) -> list[BuildingResult]:
    """Roll system rows up to buildings and return results, worst FCI first."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["building"]].append(row)
    results = []
    for building, items in grouped.items():
        deferred = sum(r["repair_cost"] for r in items)
        value = sum(r["replacement_value"] for r in items)
        worst = max(items, key=lambda r: r["repair_cost"] / r["replacement_value"] if r["replacement_value"] else 0)
        fci = compute_fci(deferred, value)
        results.append(BuildingResult(building, deferred, value, fci, rate(fci, bands), worst["system"]))
    return sorted(results, key=lambda r: (-r.fci, r.building))


def format_text(results: list[BuildingResult]) -> str:
    """Render results as a fixed-width table."""
    lines = [f"{'Building':<12}{'Deferred':>12}{'Value':>14}{'FCI':>8}  {'Rating':<9}Worst system"]
    for r in results:
        lines.append(
            f"{r.building:<12}{r.deferred_maintenance:>12,.0f}{r.replacement_value:>14,.0f}"
            f"{r.fci:>8.1%}  {r.rating:<9}{r.worst_system}"
        )
    return "\n".join(lines)


def format_markdown(results: list[BuildingResult]) -> str:
    """Render results as a Markdown report table."""
    lines = [
        "| Building | Deferred maintenance | Replacement value | FCI | Rating | Worst system |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.building} | {r.deferred_maintenance:,.0f} | {r.replacement_value:,.0f} "
            f"| {r.fci:.1%} | {r.rating} | {r.worst_system} |"
        )
    return "\n".join(lines)
