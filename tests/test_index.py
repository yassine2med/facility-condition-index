from pathlib import Path

import pytest

from fci.__main__ import main
from fci.index import analyze, compute_fci, format_markdown, format_text, rate, read_systems

EX = Path(__file__).resolve().parent.parent / "examples" / "systems.csv"


def test_compute_fci_basic():
    assert compute_fci(50_000, 1_000_000) == pytest.approx(0.05)


def test_zero_deferred_is_zero():
    assert compute_fci(0, 100.0) == 0.0


def test_zero_or_negative_value_rejected():
    with pytest.raises(ValueError):
        compute_fci(1, 0)
    with pytest.raises(ValueError):
        compute_fci(1, -5)


def test_negative_deferred_rejected():
    with pytest.raises(ValueError):
        compute_fci(-1, 100)


@pytest.mark.parametrize(
    "value,label",
    [(0.0, "Good"), (0.05, "Good"), (0.0501, "Fair"), (0.10, "Fair"), (0.2, "Poor"), (0.30, "Poor"), (0.31, "Critical")],
)
def test_rating_bands(value, label):
    assert rate(value) == label


def test_custom_bands():
    assert rate(0.2, ((0.25, "OK"),)) == "OK"
    assert rate(0.3, ((0.25, "OK"),)) == "Critical"


def test_read_example_rows():
    rows = read_systems(EX)
    assert len(rows) == 10
    assert rows[0]["system"] == "HVAC"


def test_analyze_rolls_up_and_sorts_worst_first():
    results = analyze(read_systems(EX))
    assert [r.building for r in results] == ["Building C", "Building A", "Building B"]
    a = next(r for r in results if r.building == "Building A")
    assert a.deferred_maintenance == 277_000
    assert a.replacement_value == 2_300_000
    assert a.rating == "Poor"


def test_worst_system_is_highest_ratio():
    results = analyze(read_systems(EX))
    assert results[0].worst_system == "HVAC"


def test_building_with_zero_repairs_is_good():
    rows = [{"building": "X", "system": "HVAC", "repair_cost": 0.0, "replacement_value": 100.0}]
    assert analyze(rows)[0].rating == "Good"


def test_bad_row_reports_row_number(tmp_path):
    path = tmp_path / "s.csv"
    path.write_text("building,system,repair_cost,replacement_value\nA,HVAC,abc,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row 1"):
        read_systems(path)


def test_zero_value_building_rejected():
    rows = [{"building": "X", "system": "HVAC", "repair_cost": 5.0, "replacement_value": 0.0}]
    with pytest.raises(ValueError):
        analyze(rows)


def test_formats_contain_all_buildings():
    results = analyze(read_systems(EX))
    assert all(b in format_text(results) for b in ("Building A", "Building B", "Building C"))
    assert format_markdown(results).startswith("| Building |")


def test_cli(capsys, tmp_path):
    assert main([str(EX)]) == 0
    assert main([str(EX), "--format", "md"]) == 0
    assert main([str(tmp_path / "none.csv")]) == 1
    empty = tmp_path / "e.csv"
    empty.write_text("building,system,repair_cost,replacement_value\n", encoding="utf-8")
    assert main([str(empty)]) == 1
