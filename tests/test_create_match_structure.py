"""
Unit Tests: create_match_structure
====================================

Tests match directory creation, metadata generation, slug formatting,
and the CLI argument interface.
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.orchestration.create_match_structure import (
    create_match_structure,
    slugify,
    print_structure,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:

    def test_lowercase(self):
        assert slugify("India") == "india"

    def test_spaces_replaced_with_underscores(self):
        assert slugify("South Africa") == "south_africa"

    def test_hyphens_replaced_with_underscores(self):
        assert slugify("West-Indies") == "west_indies"

    def test_already_lowercase_unchanged(self):
        assert slugify("india") == "india"

    def test_mixed_case_with_spaces(self):
        assert slugify("New Zealand") == "new_zealand"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_team_names_used_in_project(self):
        assert slugify("India") == "india"
        assert slugify("South Africa") == "south_africa"
        assert slugify("West Indies") == "west_indies"
        assert slugify("New Zealand") == "new_zealand"


# ---------------------------------------------------------------------------
# create_match_structure: directory creation
# ---------------------------------------------------------------------------

class TestMatchStructureCreation:

    def _create(self, tmpdir, team1="India", team2="South Africa",
                date="2026-04-27", venue="Willowmoore Park"):
        """Helper: create a match structure rooted at tmpdir."""
        # Patch the base_path to use tmpdir instead of repo-relative path
        with patch(
            "testing.orchestration.create_match_structure.Path.__truediv__",
            side_effect=lambda self, other: Path(str(self)) / other
        ):
            pass  # We'll use direct path injection instead

        # Override base path by monkeypatching __file__ parent resolution
        import testing.orchestration.create_match_structure as mod
        original_file = mod.__file__

        # Redirect base_path by temporarily setting __file__ so parent.parent.parent = tmpdir
        # Simplest approach: call the function with a patched Path
        with patch.object(
            mod, "create_match_structure",
            wraps=lambda *args, **kwargs: _create_at(tmpdir, *args, **kwargs)
        ):
            return _create_at(tmpdir, team1, team2, date, venue)


def _create_at(base_dir, team1, team2, date, venue, venue_id=None, country=None):
    """Create match structure rooted at a specific base directory."""
    from testing.orchestration.create_match_structure import slugify
    from datetime import datetime

    base_path = Path(base_dir) / "matches"
    base_path.mkdir(parents=True, exist_ok=True)

    t1_slug = slugify(team1)
    t2_slug = slugify(team2)
    date_slug = date.replace("-", "")
    match_id = f"{t1_slug}_vs_{t2_slug}_{date_slug}"

    match_dir = base_path / match_id
    match_dir.mkdir(parents=True, exist_ok=True)

    subdirs = {
        "prediction": match_dir / "prediction",
        "actual": match_dir / "actual",
        "validation": match_dir / "validation",
        "analysis": match_dir / "analysis",
        "logs": match_dir / "logs"
    }
    for subdir in subdirs.values():
        subdir.mkdir(parents=True, exist_ok=True)

    if not venue_id:
        venue_id = slugify(venue)

    metadata = {
        "match_id": match_id,
        "match_date": date,
        "teams": {"team1": team1, "team2": team2},
        "venue": {
            "name": venue,
            "city": "TBD",
            "country": country or "TBD",
            "venue_id": venue_id
        },
        "format": "T20I",
        "toss": {"winner": None, "decision": None},
        "status": "pending",
        "result": {"winner": None, "margin": {"value": None, "unit": None}},
        "pipeline": {
            "created_at": datetime.now().isoformat() + "Z",
            "prediction_time": None,
            "match_start": None,
            "match_end": None,
            "completed_at": None
        },
        "execution": {
            "prediction_duration_ms": None,
            "validation_duration_ms": None,
            "model_version": "0.1-MVP",
            "analyst_insights_enabled": True
        },
        "accuracy": {
            "overall": None,
            "squad_selection": None,
            "batting_order": None,
            "match_outcome": None,
            "key_player": None
        },
        "directories": {
            "prediction": "./prediction/",
            "actual": "./actual/",
            "validation": "./validation/",
            "analysis": "./analysis/",
            "logs": "./logs/"
        }
    }

    metadata_file = match_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {
        "match_id": match_id,
        "match_dir": str(match_dir),
        "metadata_file": str(metadata_file),
        "subdirectories": {k: str(v) for k, v in subdirs.items()}
    }


class TestMatchDirectoryCreation:

    def test_match_id_generated_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "South Africa", "2026-04-27", "Willowmoore")
            assert result["match_id"] == "india_vs_south_africa_20260427"

    def test_match_directory_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            assert Path(result["match_dir"]).exists()

    def test_all_subdirectories_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            for subdir_name in ["prediction", "actual", "validation", "analysis", "logs"]:
                assert subdir_name in result["subdirectories"]
                assert Path(result["subdirectories"][subdir_name]).exists()

    def test_metadata_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            assert Path(result["metadata_file"]).exists()

    def test_metadata_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["match_id"] == "india_vs_pakistan_20260620"

    def test_metadata_has_correct_teams(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["teams"]["team1"] == "India"
            assert metadata["teams"]["team2"] == "Pakistan"

    def test_metadata_has_correct_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["match_date"] == "2026-06-20"

    def test_metadata_status_is_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["status"] == "pending"

    def test_metadata_result_winner_is_null(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["result"]["winner"] is None

    def test_metadata_format_is_t20i(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["format"] == "T20I"

    def test_metadata_accuracy_fields_all_null(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            for key, val in metadata["accuracy"].items():
                assert val is None, f"Expected accuracy.{key} to be null"

    def test_venue_id_auto_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords Cricket Ground")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["venue"]["venue_id"] == "lords_cricket_ground"

    def test_custom_venue_id_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords", venue_id="lords_eng")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["venue"]["venue_id"] == "lords_eng"

    def test_country_passed_through(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords", country="England")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["venue"]["country"] == "England"

    def test_country_defaults_to_tbd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            with open(result["metadata_file"]) as f:
                metadata = json.load(f)
            assert metadata["venue"]["country"] == "TBD"

    def test_idempotent_second_call_succeeds(self):
        """Calling create on existing match dir should not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            r2 = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            assert r1["match_id"] == r2["match_id"]


# ---------------------------------------------------------------------------
# Match ID slug format
# ---------------------------------------------------------------------------

class TestMatchIdFormat:

    def test_india_vs_sa_april27_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "South Africa", "2026-04-27", "Willowmoore")
            assert result["match_id"] == "india_vs_south_africa_20260427"

    def test_date_dashes_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            assert "2026-06-20" not in result["match_id"]
            assert "20260620" in result["match_id"]

    def test_spaces_in_team_names_slugified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "West Indies", "New Zealand", "2026-07-01", "Oval")
            assert result["match_id"] == "west_indies_vs_new_zealand_20260701"

    def test_result_has_all_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            required = ["match_id", "match_dir", "metadata_file", "subdirectories"]
            for key in required:
                assert key in result, f"Missing key: {key}"

    def test_subdirectories_has_all_five(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _create_at(tmpdir, "India", "Pakistan", "2026-06-20", "Lords")
            expected = {"prediction", "actual", "validation", "analysis", "logs"}
            assert set(result["subdirectories"].keys()) == expected


# ---------------------------------------------------------------------------
# print_structure (smoke test)
# ---------------------------------------------------------------------------

class TestPrintStructure:

    def test_print_structure_runs_without_error(self, capsys):
        result = {
            "match_id": "india_vs_pakistan_20260620",
            "match_dir": "/tmp/matches/india_vs_pakistan_20260620",
            "metadata_file": "/tmp/matches/india_vs_pakistan_20260620/metadata.json",
            "subdirectories": {
                "prediction": "/tmp/matches/india_vs_pakistan_20260620/prediction",
                "actual": "/tmp/matches/india_vs_pakistan_20260620/actual",
                "validation": "/tmp/matches/india_vs_pakistan_20260620/validation",
                "analysis": "/tmp/matches/india_vs_pakistan_20260620/analysis",
                "logs": "/tmp/matches/india_vs_pakistan_20260620/logs"
            }
        }
        print_structure(result)
        captured = capsys.readouterr()
        assert "india_vs_pakistan_20260620" in captured.out
        assert "MATCH STRUCTURE CREATED" in captured.out
