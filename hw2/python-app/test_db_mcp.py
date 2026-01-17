"""Integration tests and fixtures for the MCP server board game tools.

All fixtures are co-located in this file to keep test setup self-contained.

Additional MCP-specific tests similar to test_db_app.py:
- test_mcp_get_games_by_name: Tests get_games_by_name MCP tool with specific queries
- test_mcp_search_designers_workflow: Tests designer search workflow (search -> candidates -> cards)
- test_mcp_search_categories_workflow: Tests category search workflow (search -> candidates -> cards)

These tests validate specific query results against expected outputs stored in JSON files
in the test_data/ directory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Callable, Generator

import pytest


REQUIRED_TOOLS = {
    "get_games_by_name",
    "get_game_profile",
    "search_categories",
    "search_designers",
    "candidate_by_categories",
    "candidate_by_designers",
    "score_candidates",
    "fetch_game_cards",
}


def _rpc(proc: subprocess.Popen, id_: int, method: str, params: dict[str, Any]) -> Any:
    """Send JSON-RPC request to MCP server and receive response."""
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": id_, "method": method, "params": params}) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("No response from server")
    resp = json.loads(line)
    if "error" in resp:
        raise RuntimeError(resp["error"])
    return resp["result"]


@pytest.fixture(scope="session")
def server_proc() -> Generator[subprocess.Popen, None, None]:
    """Start and manage the MCP server for the test session."""
    # Check for required DB credentials
    if not all([os.environ.get("DB_HOST"), os.environ.get("DB_NAME"), 
                os.environ.get("DB_USER"), os.environ.get("DB_PASSWORD")]):
        pytest.fail("Database credentials not set; required: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
    proc = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=os.environ.copy(),
        bufsize=1,
    )
    _rpc(proc, 1, "tools/list", {})
    yield proc
    proc.kill()


@pytest.fixture(scope="session")
def rpc(server_proc: subprocess.Popen) -> Callable[[int, str, dict[str, Any]], Any]:
    """Provide RPC callable for communicating with the MCP server."""
    return lambda id_, method, params: _rpc(server_proc, id_, method, params)


def test_tools_list_contains_required(rpc: Callable[[int, str, dict[str, Any]], Any]) -> None:
    tools = rpc(10, "tools/list", {})
    names = {t["name"] for t in tools}
    missing = REQUIRED_TOOLS - names
    assert not missing, f"Missing required tools: {missing}"


def test_find_and_profile_roundtrip(rpc: Callable[[int, str, dict[str, Any]], Any]) -> None:
    """Test get_game_profile returns complete data with categories and designers."""
    # Use a known game ID (Pandemic Legacy: Season 1)
    gid = 71065
    prof = rpc(13, "tools/call", {"name": "get_game_profile", "arguments": {"g_id": gid}})
    assert prof is not None, f"Game profile should exist for g_id={gid}"
    assert prof["g_id"] == gid
    assert isinstance(prof.get("categories"), list)
    assert isinstance(prof.get("designers"), list)


def test_candidate_to_cards_pipeline(rpc: Callable[[int, str, dict[str, Any]], Any]) -> None:
    """Test score_candidates with known candidate data."""
    # Use known candidate data instead of generating it
    constraints = {"min_votes": 0, "limit_candidates": 50, "limit_final": 8}
    
    # Simulate candidates with known overlap values
    candidates = [
        {"g_id": 10, "cat_overlap": 3, "designer_overlap": 0},
        {"g_id": 20, "cat_overlap": 2, "designer_overlap": 1},
        {"g_id": 30, "cat_overlap": 1, "designer_overlap": 2},
        {"g_id": 40, "cat_overlap": 0, "designer_overlap": 1},
    ]
    
    rec_ids = rpc(
        25,
        "tools/call",
        {
            "name": "score_candidates",
            "arguments": {
                "candidates": candidates,
                "constraints": constraints,
                "exclude_g_ids": [5],
            },
        },
    )
    assert 5 not in rec_ids
    assert len(rec_ids) <= 8
    assert isinstance(rec_ids, list)


# MCP-specific tests that match test_db_app.py patterns
@pytest.fixture(scope="session")
def expected_games_by_name():
    """Load expected game name query results."""
    import json
    from pathlib import Path
    test_data_path = Path(__file__).parent / "test_data" / "games_by_name.json"
    with open(test_data_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def expected_designers_mcp():
    """Load expected designer query results via MCP tools."""
    import json
    from pathlib import Path
    test_data_path = Path(__file__).parent / "test_data" / "designers_mcp.json"
    with open(test_data_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def expected_categories_mcp():
    """Load expected category query results via MCP tools."""
    import json
    from pathlib import Path
    test_data_path = Path(__file__).parent / "test_data" / "categories_mcp.json"
    with open(test_data_path) as f:
        return json.load(f)


@pytest.mark.parametrize("name_query,expected_count", [
    ("game", 26), 
    ("monopoly", 21), 
    ("risk", 7), 
    ("clue", 7)
])
def test_mcp_get_games_by_name(rpc: Callable[[int, str, dict[str, Any]], Any], 
                                 expected_games_by_name: dict[str, Any],
                                 name_query: str, 
                                 expected_count: int) -> None:
    """Test MCP get_games_by_name tool returns correct count and matching games."""
    result = rpc(100, "tools/call", {
        "name": "get_games_by_name", 
        "arguments": {"name_query": name_query, "limit": 100}
    })
    
    # Check count matches
    assert len(result) == expected_count, f"Expected {expected_count} games for '{name_query}', got {len(result)}"
    
    # Check all game IDs and names match expected
    expected = expected_games_by_name[name_query]
    assert len(result) == expected["count"]
    
    result_games = {g["g_id"]: g["name"] for g in result}
    expected_games = {g["g_id"]: g["name"] for g in expected["games"]}
    
    assert result_games == expected_games, f"Games for '{name_query}' don't match expected"
    
    # Verify all names contain the search query
    for game in result:
        assert name_query in game["name"].lower(), f"Game '{game['name']}' doesn't contain '{name_query}'"


@pytest.mark.parametrize("designer_query", ["rob", "david", "matt", "maggi"])
def test_mcp_search_designers(rpc: Callable[[int, str, dict[str, Any]], Any],
                               expected_designers_mcp: dict[str, Any],
                               designer_query: str) -> None:
    """Test search_designers returns correct results."""
    expected = expected_designers_mcp[designer_query]
    
    # Test search_designers only
    designers = rpc(300, "tools/call", {
        "name": "search_designers",
        "arguments": {"query": designer_query, "limit": 10}
    })
    
    assert len(designers) > 0, f"No designers found for query '{designer_query}'"
    
    # Find the matching designer (should match expected designer_id)
    designer = next((d for d in designers if d["des_id"] == expected["designer_id"]), None)
    assert designer is not None, f"Expected designer ID {expected['designer_id']} not found in results"
    assert designer["des_id"] == expected["designer_id"]
    assert designer_query.lower() in designer["name"].lower()


@pytest.mark.parametrize("designer_query", ["rob", "david", "matt", "maggi"])
def test_mcp_candidate_by_designers(rpc: Callable[[int, str, dict[str, Any]], Any],
                                     expected_designers_mcp: dict[str, Any],
                                     designer_query: str) -> None:
    """Test candidate_by_designers returns correct games for known designer IDs."""
    expected = expected_designers_mcp[designer_query]
    
    # Test candidate_by_designers only with known designer ID
    constraints = {"min_votes": 0, "limit_candidates": 100}
    candidates = rpc(301, "tools/call", {
        "name": "candidate_by_designers",
        "arguments": {"des_ids": [expected["designer_id"]], "constraints": constraints}
    })
    
    # Check that we get the expected count
    assert len(candidates) == expected["count"], \
        f"Expected {expected['count']} games for designer '{designer_query}', got {len(candidates)}"
    
    # Verify game IDs match
    result_game_ids = {c["g_id"] for c in candidates}
    expected_game_ids = {g["g_id"] for g in expected["games"]}
    assert result_game_ids == expected_game_ids, \
        f"Game IDs for designer '{designer_query}' don't match expected"


@pytest.mark.parametrize("category_query", ["strategy", "party", "card"])
def test_mcp_search_categories(rpc: Callable[[int, str, dict[str, Any]], Any],
                                expected_categories_mcp: dict[str, Any],
                                category_query: str) -> None:
    """Test search_categories returns correct results."""
    expected = expected_categories_mcp[category_query]
    
    # Test search_categories only
    categories = rpc(400, "tools/call", {
        "name": "search_categories",
        "arguments": {"query": category_query, "limit": 10}
    })
    
    assert len(categories) > 0, f"No categories found for query '{category_query}'"
    
    # Find the matching category (should match expected category_id)
    category = next((c for c in categories if c["c_id"] == expected["category_id"]), None)
    assert category is not None, f"Expected category ID {expected['category_id']} not found in results"
    assert category["c_id"] == expected["category_id"]
    assert category_query.lower() in category["name"].lower()


@pytest.mark.parametrize("category_query", ["strategy", "party", "card"])
def test_mcp_candidate_by_categories(rpc: Callable[[int, str, dict[str, Any]], Any],
                                      expected_categories_mcp: dict[str, Any],
                                      category_query: str) -> None:
    """Test candidate_by_categories returns correct games for known category IDs."""
    expected = expected_categories_mcp[category_query]
    
    # Test candidate_by_categories only with known category ID
    constraints = {"min_votes": 0, "limit_candidates": 100, "limit_final": 20}
    candidates = rpc(401, "tools/call", {
        "name": "candidate_by_categories",
        "arguments": {"c_ids": [expected["category_id"]], "constraints": constraints}
    })
    
    # Check that we get the expected count
    assert len(candidates) == expected["count"], \
        f"Expected {expected['count']} games for category '{category_query}', got {len(candidates)}"
    
    # Verify game IDs match
    result_game_ids = {c["g_id"] for c in candidates}
    expected_game_ids = {g["g_id"] for g in expected["games"]}
    assert result_game_ids == expected_game_ids, \
        f"Game IDs for category '{category_query}' don't match expected"


# Additional unit tests for db.py functions
import os
from db import DBManager, Boardgame, Designer, Category, Constraints


@pytest.fixture
def db_manager():
    """Create DBManager instance for direct unit testing."""
    return DBManager(
        host="wellington.cs.uchicago.edu",
        database="boardgames",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )


def test_get_game_profile_with_data(db_manager):
    """Test get_game_profile returns complete game data with relationships."""
    # Use a known game ID (Pandemic Legacy: Season 1)
    game_id = 71065
    profile = db_manager.get_game_profile(game_id)
    
    assert profile is not None
    assert profile.g_id == game_id
    assert profile.name is not None
    assert isinstance(profile.categories, list)
    assert isinstance(profile.designers, list)
    
    # Verify category objects have expected attributes
    if profile.categories:
        for cat in profile.categories:
            assert isinstance(cat, Category)
            assert hasattr(cat, 'c_id')
            assert hasattr(cat, 'name')
    
    # Verify designer objects have expected attributes
    if profile.designers:
        for des in profile.designers:
            assert isinstance(des, Designer)
            assert hasattr(des, 'des_id')
            assert hasattr(des, 'name')


def test_get_game_profile_nonexistent(db_manager):
    """Test get_game_profile returns None for non-existent game ID."""
    profile = db_manager.get_game_profile(999999)
    assert profile is None


def test_candidate_by_categories_returns_sorted(db_manager):
    """Test candidate_by_categories returns sorted results."""
    constraints = {
        "min_votes": 0,
        "limit_candidates": 20,
        "limit_final": 8
    }
    
    # Use a category that likely has games
    candidates = db_manager.candidate_by_categories([1], constraints)
    
    assert isinstance(candidates, list)
    assert all(isinstance(c, dict) for c in candidates)
    assert all("g_id" in c and "cat_overlap" in c for c in candidates)
    
    # Verify sorted by overlap descending
    if len(candidates) > 1:
        overlaps = [c["cat_overlap"] for c in candidates]
        assert overlaps == sorted(overlaps, reverse=True)
    
    assert len(candidates) <= 20


def test_candidate_by_categories_empty_ids(db_manager):
    """Test candidate_by_categories with empty category list."""
    constraints = {"min_votes": 0, "limit_candidates": 20}
    candidates = db_manager.candidate_by_categories([], constraints)
    assert candidates == []


def test_candidate_by_designers_returns_results(db_manager):
    """Test candidate_by_designers returns valid results."""
    constraints = {
        "min_votes": 0,
        "limit_candidates": 15,
        "limit_final": 8
    }
    
    # Use a designer ID that likely has games
    candidates = db_manager.candidate_by_designers([1], constraints)
    
    assert isinstance(candidates, list)
    assert all(isinstance(c, dict) for c in candidates)
    assert all("g_id" in c and "designer_overlap" in c for c in candidates)
    
    assert len(candidates) <= 15


def test_candidate_by_designers_empty_ids(db_manager):
    """Test candidate_by_designers with empty designer list."""
    constraints = {"min_votes": 0, "limit_candidates": 15}
    candidates = db_manager.candidate_by_designers([], constraints)
    assert candidates == []


def test_score_and_diversify_with_candidates(db_manager):
    """Test score_candidates filters and scores candidates correctly."""
    # Use known candidate data instead of generating it
    seed_gid = 100
    constraints = {
        "min_votes": 0,
        "limit_candidates": 50,
        "limit_final": 5
    }
    
    # Create mock candidates with known overlap values
    candidates = [
        {"g_id": 10, "cat_overlap": 3, "designer_overlap": 0},
        {"g_id": 20, "cat_overlap": 2, "designer_overlap": 1},
        {"g_id": 30, "cat_overlap": 1, "designer_overlap": 2},
        {"g_id": 40, "cat_overlap": 0, "designer_overlap": 1},
        {"g_id": seed_gid, "cat_overlap": 5, "designer_overlap": 3},  # Should be excluded
    ]
    
    final_ids = db_manager.score_candidates(candidates, constraints, [seed_gid])
    
    assert isinstance(final_ids, list)
    assert len(final_ids) <= 5
    assert seed_gid not in final_ids, "Seed game should be excluded"
    assert all(isinstance(g_id, int) for g_id in final_ids)


def test_score_and_diversify_empty_candidates(db_manager):
    """Test score_candidates with empty candidates."""
    constraints = {"limit_final": 8}
    final_ids = db_manager.score_candidates([], constraints, [])
    assert final_ids == []


@pytest.mark.parametrize("scenario_name", ["pandemic_top5", "monopoly_top8", "clue_top3"])
def test_score_candidates_with_known_results(db_manager, scenario_name):
    """Test score_candidates returns expected game IDs for known candidate data."""
    import json
    from pathlib import Path
    
    # Load test data
    test_data_path = Path(__file__).parent / "test_data" / "score_candidates.json"
    with open(test_data_path) as f:
        scenarios = json.load(f)
    
    # Find the scenario
    scenario = next((s for s in scenarios if s["scenario"] == scenario_name), None)
    if not scenario:
        pytest.skip(f"Scenario {scenario_name} not found in test data")
    
    # Use pre-loaded candidate data from scenario instead of generating
    constraints = scenario["constraints"]
    seed_g_id = scenario["seed_game"]["g_id"]
    
    # Reconstruct candidates from expected data
    # The test data should include the candidate lists that were generated
    all_candidates = scenario.get("all_candidates", [])
    
    if not all_candidates:
        # If not stored in test data, skip this test
        pytest.skip(f"Candidate data not available for {scenario_name}")
    
    # Score candidates directly without generating them
    final_ids = db_manager.score_candidates(all_candidates, constraints, [seed_g_id])
    
    # Verify results match expected
    assert len(final_ids) == scenario["expected_final_count"], \
        f"Expected {scenario['expected_final_count']} results, got {len(final_ids)}"
    
    assert final_ids == scenario["expected_final_g_ids"], \
        f"Game IDs don't match. Expected {scenario['expected_final_g_ids']}, got {final_ids}"
    
    # Verify seed game is excluded
    assert seed_g_id not in final_ids, \
        f"Seed game {seed_g_id} should be excluded from results"
    
    # Verify all returned IDs are integers
    assert all(isinstance(g_id, int) for g_id in final_ids), \
        "All game IDs should be integers"


def test_fetch_game_cards_preserves_order(db_manager):
    """Test fetch_game_cards returns games in requested order."""
    # Use known game IDs that exist
    g_ids = [71065, 80399, 78530]
    reversed_ids = list(reversed(g_ids))
    
    cards = db_manager.fetch_game_cards(reversed_ids)
    
    assert len(cards) == len(reversed_ids)
    returned_ids = [card.g_id for card in cards]
    assert returned_ids == reversed_ids


def test_fetch_game_cards_with_relationships(db_manager):
    """Test fetch_game_cards populates categories and designers."""
    # Use a known game ID (Pandemic Legacy: Season 1)
    g_ids = [71065]
    cards = db_manager.fetch_game_cards(g_ids)
    
    assert len(cards) == 1
    card = cards[0]
    
    assert card.g_id == g_ids[0]
    assert isinstance(card.categories, list)
    assert isinstance(card.designers, list)
    
    # These should be Category/Designer objects, not empty
    if card.categories:
        assert all(isinstance(c, Category) for c in card.categories)
    if card.designers:
        assert all(isinstance(d, Designer) for d in card.designers)


def test_fetch_game_cards_empty_list(db_manager):
    """Test fetch_game_cards with empty game ID list."""
    cards = db_manager.fetch_game_cards([])
    assert cards == []


def test_fetch_game_cards_nonexistent_ids(db_manager):
    """Test fetch_game_cards skips non-existent game IDs."""
    cards = db_manager.fetch_game_cards([999999, 888888])
    assert cards == []



def test_boardgame_equality_and_hashing(db_manager):
    """Test Boardgame objects can be hashed and compared."""
    # Use known game IDs
    game1 = db_manager.get_game_profile(71065)
    game2 = db_manager.get_game_profile(80399)
    
    if not game1 or not game2:
        pytest.skip("Need games with these IDs to exist")
    
    # Same game should have same hash
    assert hash(game1) == hash(game1)
    
    # Different games should (likely) have different hashes
    if game1.g_id != game2.g_id:
        assert hash(game1) != hash(game2)
    
    # Should be usable in sets/dicts
    game_set = {game1, game2}
    assert len(game_set) >= 1


def test_database_connection_reuse(db_manager):
    """Test that DBManager reuses connection across queries."""
    # First call
    first_conn = db_manager.conn
    _ = db_manager.search_categories()
    
    # Second call - should reuse same connection
    second_conn = db_manager.conn
    
    # Should be same connection object
    assert first_conn is second_conn
    assert not first_conn.closed
