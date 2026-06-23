"""Tests for the Phase-2 full Nixtla model catalog (P2 catalog)."""

from __future__ import annotations

from tsforecasting.models.catalog import (
    CATALOG,
    CatalogEntry,
    generate_catalog_md,
    list_catalog,
)

_MVP_PRESETS = {
    "seasonal_naive",
    "auto_ets",
    "linear_regression",
    "ridge",
    "lasso",
    "elastic_net",
    "random_forest",
    "hist_gradient_boosting",
    "nhits",
    "nbeats",
}


def test_catalog_covers_three_backends() -> None:
    backends = {e.backend for e in CATALOG}
    assert {"statsforecast", "mlforecast", "neuralforecast"} <= backends
    # substantive coverage of the official model directories
    assert sum(1 for e in CATALOG if e.backend == "statsforecast") >= 25
    assert sum(1 for e in CATALOG if e.backend == "neuralforecast") >= 25
    assert sum(1 for e in CATALOG if e.backend == "mlforecast") >= 6


def test_every_entry_has_source_url_and_known_status() -> None:
    valid_status = {"cataloged", "mvp_smoke", "validated", "blocked", "deprecated"}
    for e in CATALOG:
        assert isinstance(e, CatalogEntry)
        assert e.source_url.startswith("https://"), e
        assert e.status in valid_status, e
        assert e.dependency_group in {"core", "ml", "neural"}, e


def test_mvp_presets_marked_smoke() -> None:
    by_name = {e.name: e for e in CATALOG}
    for name in _MVP_PRESETS:
        assert name in by_name, name
        assert by_name[name].status == "mvp_smoke", name


def test_names_unique_per_backend() -> None:
    seen: set[tuple[str, str]] = set()
    for e in CATALOG:
        key = (e.backend, e.name)
        assert key not in seen, key
        seen.add(key)


def test_list_catalog_filters() -> None:
    neural = list_catalog(backend="neuralforecast")
    assert all(e.backend == "neuralforecast" for e in neural)
    smoke = list_catalog(status="mvp_smoke")
    assert {e.name for e in smoke} == _MVP_PRESETS
    assert all(e.status == "mvp_smoke" for e in smoke)


def test_generate_catalog_md_contains_sections_and_a_model() -> None:
    md = generate_catalog_md()
    assert "# Model catalog" in md
    assert "statsforecast" in md
    assert "neuralforecast" in md
    assert "mlforecast" in md
    assert "seasonal_naive" in md
    # every catalog entry appears by name
    for e in CATALOG:
        assert e.name in md
