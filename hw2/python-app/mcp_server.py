"""Minimal MCP-compatible JSON-RPC server for board game recommendations.

Implements a lightweight Model Context Protocol server that communicates via
JSON-RPC over stdin/stdout without external dependencies. Provides tool listing
and execution capabilities.

Methods:
    - tools/list: List all available MCP tools
    - tools/call: Execute a tool with specified parameters
"""

from __future__ import annotations
from typing import Any
import logging
import os
import sys
import json

from db import DBManager, Boardgame

# Configure logging to file with debug level
log_file = '/tmp/mcp_server_debug.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stderr)
    ],
    force=True
)
logger = logging.getLogger(__name__)
logger.info(f"=== MCP Server Started - Logging to {log_file} ===")

# Constraints documentation string for tool descriptions
CONSTRAINTS_DOC = (
    "Constraints object with optional fields: "
    "players (int, exact player count), "
    "minplayers (int, minimum players), "
    "maxplayers (int, maximum players), "
    "minplaytime (int, minimum playtime in minutes), "
    "maxplaytime (int, maximum playtime in minutes), "
    "min_votes (int, default 500, minimum rating votes), "
    "limit_candidates (int, default 200, max candidates per generator), "
    "limit_final (int, default 8, number of final recommendations)"
)


def _to_json_serializable(obj: Any) -> Any:
    """Convert model objects to JSON-serializable format.
    
    Args:
        obj: Object to convert (Boardgame, list, dict, etc.).
        
    Returns:
        JSON-serializable representation.
    """
    if isinstance(obj, list):
        return [_to_json_serializable(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    else:
        return obj


def _jsonable(x: Any) -> Any:
    """Validate and convert object to JSON serializable format.
    
    Handles model objects by converting them to dictionaries.
    
    Args:
        x: Object to validate and convert.
        
    Returns:
        JSON-serializable object.
        
    Raises:
        TypeError: If object cannot be serialized.
    """
    converted = _to_json_serializable(x)
    json.dumps(converted)  # Validate it's serializable
    return converted


def _error(id_: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    """Build a JSON-RPC error response.
    
    Args:
        id_: Request ID to echo back.
        code: JSON-RPC error code.
        message: Human-readable error message.
        data: Optional error data dictionary.
        
    Returns:
        JSON-RPC error response dictionary.
    """
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


def _ok(id_: Any, result: Any) -> dict[str, Any]:
    """Build a JSON-RPC success response.
    
    Args:
        id_: Request ID to echo back.
        result: Result data.
        
    Returns:
        JSON-RPC success response dictionary.
    """
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def main() -> None:
    """Run the MCP JSON-RPC server.
    
    Reads JSON-RPC requests from stdin, dispatches to tool implementations,
    and writes responses to stdout. Requires database credentials via
    environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD.
    
    Supported tools:
        - get_games_by_name: Search games by name
        - get_game_profile: Fetch game profile with categories and designers
        - candidate_by_categories: Generate candidates by category
        - candidate_by_designers: Generate candidates by designer
        - score_candidates: Score and select final recommendations
        - fetch_game_cards: Fetch final game cards for display
        
    Exits with code 2 if required database credentials are not set.
    """
    # Get database connection parameters from environment variables
    host = os.environ.get("DB_HOST")
    database = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    port = int(os.environ.get("DB_PORT", "5432"))
    
    if not all([host, database, user, password]):
        logger.error("Database credentials not set. Required: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        print(json.dumps(_error(None, -32000, "Database credentials not set")), flush=True)
        sys.exit(2)

    logger.info("Initializing database connection...")
    # Type guards: we've checked that all values are not None/empty above
    db = DBManager(
        host=host,  # type: ignore[arg-type]
        database=database,  # type: ignore[arg-type]
        user=user,  # type: ignore[arg-type]
        password=password,  # type: ignore[arg-type]
        port=port
    )
    logger.info("Database connection established")

    tools: dict[str, dict[str, Any]] = {
        "get_games_by_name": {
            "description": "Find games by (substring) name.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "name_query":{"type":"string"},
                    "limit":{"type":"integer","default":10}
                },
                "required":["name_query"]
            },
            "fn": lambda name_query, limit=10, **kwargs: db.get_games_by_name(name_query, limit),
        },
        "get_game_profile": {
            "description": "Fetch a denormalized game profile (stats + categories + designers).",
            "inputSchema": {"type":"object","properties":{"g_id":{"type":"integer"}}, "required":["g_id"]},
            "fn": lambda g_id, **kwargs: db.get_game_profile(int(g_id)),
        },
        "search_categories": {
            "description": "Search for categories by name substring. Omit query to list all categories.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "query":{"type":"string", "description":"Category name substring to search for (optional - omit to list all)"},
                    "limit":{"type":"integer","default":10}
                },
                "required":[]
            },
            "fn": lambda query=None, limit=10, **kwargs: db.search_categories(query, limit),
        },
        "search_designers": {
            "description": "Search for designers by name substring. Omit query to list all designers.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "query":{"type":"string", "description":"Designer name substring to search for (optional - omit to list all)"},
                    "limit":{"type":"integer","default":10}
                },
                "required":[]
            },
            "fn": lambda query=None, limit=10, **kwargs: db.search_designers(query, limit),
        },
        "candidate_by_categories": {
            "description": "Generate candidates by category overlap. Use search_categories first to get category IDs from names.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "c_ids":{"type":"array","items":{"type":"integer"}, "description":"Array of category IDs"},
                    "constraints":{"type":"object", "description":CONSTRAINTS_DOC}
                },
                "required":["c_ids", "constraints"]
            },
            "fn": lambda c_ids, constraints=None, **kwargs: db.candidate_by_categories(c_ids, constraints),
        },
        "candidate_by_designers": {
            "description": "Generate candidates by designer overlap. Use search_designers first to get designer IDs from names.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "des_ids":{"type":"array","items":{"type":"integer"}, "description":"Array of designer IDs"},
                    "constraints":{"type":"object", "description":CONSTRAINTS_DOC}
                },
                "required":["des_ids", "constraints"]
            },
            "fn": lambda des_ids, constraints=None, **kwargs: db.candidate_by_designers(des_ids, constraints),
        },
        "score_candidates": {
            "description": "Combine candidate signals, score to select final IDs.",
            "inputSchema": {
                "type":"object",
                "properties":{
                    "candidates":{"type":"array","items":{"type":"object"}},
                    "constraints":{"type":"object", "description":CONSTRAINTS_DOC},
                    "exclude_g_ids":{"type":"array","items":{"type":"integer"}}
                },
                "required":["candidates","constraints","exclude_g_ids"]
            },
            "fn": lambda candidates, constraints, exclude_g_ids, **kwargs: db.score_candidates(candidates, constraints, exclude_g_ids),
        },
        "fetch_game_cards": {
            "description": "Fetch final denormalized game cards for display.",
            "inputSchema": {"type":"object","properties":{"g_ids":{"type":"array","items":{"type":"integer"}}}, "required":["g_ids"]},
            "fn": lambda g_ids, **kwargs: db.fetch_game_cards(g_ids),
        }
    }

    logger.info(f"MCP server ready with {len(tools)} tools")
    logger.info("Waiting for JSON-RPC requests on stdin...")
    logger.debug(f"Available tools: {', '.join(tools.keys())}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {line[:100]}...")
            print(json.dumps(_error(None, -32700, "Parse error", {"line": line})), flush=True)
            continue

        id_ = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        logger.info(f"Received request: id={id_}, method={method}")

        try:
            if method == "tools/list":
                logger.info("Listing available tools")
                result = [{"name": name, "description": meta["description"], "inputSchema": meta["inputSchema"]} for name, meta in tools.items()]
                print(json.dumps(_ok(id_, result)), flush=True)
                continue

            if method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if name not in tools:
                    logger.warning(f"Unknown tool requested: {name}")
                    print(json.dumps(_error(id_, -32601, f"Unknown tool: {name}")), flush=True)
                    continue
                logger.info(f"Executing tool: {name}")
                logger.debug(f"Tool arguments: {arguments}")
                out = tools[name]["fn"](**arguments)
                logger.info(f"Tool {name} completed successfully")
                logger.debug(f"Tool {name} Output: {out}")
                print(json.dumps(_ok(id_, _jsonable(out))), flush=True)
                continue

            logger.warning(f"Unknown method: {method}")
            print(json.dumps(_error(id_, -32601, f"Unknown method: {method}")), flush=True)

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            print(json.dumps(_error(id_, -32001, "Tool error", {"error": str(e)})), flush=True)


if __name__ == "__main__":
    main()

