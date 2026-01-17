"""Board game Database Manager.

The DBManager class provides methods to connect to the PostgreSQL database,
perform schema queries, search for games, retrieve game profiles, generate
candidates, score and diversify recommendations, and fetch final game cards.

In the first part of the assignment, you will implement simple methods
to query the database schema and search for games by name or designer, which
will be used by app.py.

In the second part, you will implement more complex functionalty, and will
essentially provide database interface to an MCP (Model Context Protocol Server).
This means you will implement the core recommendation logic including schema queries,
game searches, profile retrieval, candidate generation, scoring, and final
game card fetching. It also contains lightweight data helpers for database
connections and search constraints to keep the MCP server dependency-light.

All database-acting functions are consolidated into the DBManager class so the
server can operate with a single stateful instance.
"""

import math
from typing import Any

import psycopg2
from psycopg2.extensions import connection


class Boardgame:
    """Represents a board game with its core attributes.
    
    Attributes:
        g_id: Unique game identifier.
        name: Name of the board game.
        avgscore: Average rating score.
        numvotes: Number of votes/ratings.
        minplayers: Minimum number of players.
        maxplayers: Maximum number of players.
        minplaytime: Minimum playtime in minutes.
        maxplaytime: Maximum playtime in minutes.
        categories: List of category names or Category objects.
        designers: List of designer names or Designer objects.
    """
    
    def __init__(
        self,
        g_id: int,
        name: str,
        avgscore: float | None = None,
        numvotes: int | None = None,
        minplayers: int | None = None,
        maxplayers: int | None = None,
        minplaytime: int | None = None,
        maxplaytime: int | None = None,
        categories: list[Any] | None = None,
        designers: list[Any] | None = None,
    ) -> None:
        """Initialize Boardgame object."""
        self.g_id = g_id
        self.name = name
        self.avgscore = avgscore
        self.numvotes = numvotes
        self.minplayers = minplayers
        self.maxplayers = maxplayers
        self.minplaytime = minplaytime
        self.maxplaytime = maxplaytime
        self.categories = categories or []
        self.designers = designers or []
    
    def __repr__(self) -> str:
        return f"Boardgame({self.name} (ID: {self.g_id}))"
    
    def __hash__(self) -> int:
        return hash(self.g_id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "g_id": self.g_id,
            "name": self.name,
            "avgscore": self.avgscore,
            "numvotes": self.numvotes,
            "minplayers": self.minplayers,
            "maxplayers": self.maxplayers,
            "minplaytime": self.minplaytime,
            "maxplaytime": self.maxplaytime,
            "categories": [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.categories],
            "designers": [d.to_dict() if hasattr(d, 'to_dict') else d for d in self.designers],
        }


class Designer:
    """Represents a board game designer.
    
    Attributes:
        des_id: Unique designer identifier.
        name: Designer's name.
        country: Designer's country.
    """
    
    def __init__(self, des_id: int, name: str, country: str | None = None) -> None:
        """Initialize Designer object."""
        self.des_id = des_id
        self.name = name
        self.country = country
    
    def __repr__(self) -> str:
        return f"Designer({self.name} (ID: {self.des_id}))"
    
    def __hash__(self) -> int:
        return hash(self.des_id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "des_id": self.des_id,
            "name": self.name,
            "country": self.country,
        }


class Category:
    """Represents a board game category.
    
    Attributes:
        c_id: Unique category identifier.
        name: Category name.
    """
    
    def __init__(self, c_id: int, name: str) -> None:
        """Initialize Category object."""
        self.c_id = c_id
        self.name = name
    
    def __repr__(self) -> str:
        return f"Category({self.name} (ID: {self.c_id}))"
    
    def __hash__(self) -> int:
        return hash(self.c_id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "c_id": self.c_id,
            "name": self.name,
        }


class Constraints:
    """Search constraints for filtering board games.

    All player and playtime constraints are optional. Games are filtered
    to match the specified criteria. The min_votes threshold ensures only
    sufficiently-rated games are considered.

    Attributes:
        players: Exact player count the game must support. If specified,
            game's minplayers <= players <= maxplayers.
        minplayers: Minimum players supported by returned games.
        maxplayers: Maximum players supported by returned games.
        maxplaytime: Maximum allowed maxplaytime in minutes.
        minplaytime: Minimum allowed minplaytime in minutes.
        min_votes: Minimum numvotes threshold for game inclusion.
            Defaults to 500 to ensure popularity/rating reliability.
        limit_candidates: Maximum number of candidate games per generator.
            Defaults to 200.
        limit_final: Number of final recommendations to return.
            Defaults to 8.
    """

    def __init__(
        self,
        players: int | None = None,
        minplayers: int | None = None,
        maxplayers: int | None = None,
        maxplaytime: int | None = None,
        minplaytime: int | None = None,
        min_votes: int = 500,
        limit_candidates: int = 200,
        limit_final: int = 8,
        **kwargs: Any,
    ) -> None:
        """Initialize Constraints object."""
        self.players = players
        self.minplayers = minplayers
        self.maxplayers = maxplayers
        self.minplaytime = minplaytime
        self.maxplaytime = maxplaytime
        self.min_votes = min_votes
        self.limit_candidates = limit_candidates
        self.limit_final = limit_final


class DBManager:
    """Database tool for board game recommendation queries.
    
    Manages a persistent database connection and provides methods for
    searching games, generating recommendations, and fetching game profiles.
    Uses PostgreSQL-specific features and maintains connection pooling.
    
    Attributes:
        host: Database server hostname.
        port: Database server port.
        database: Database name.
        user: Database username.
        password: Database password.
        statement_timeout_ms: Query timeout in milliseconds.
        conn: Persistent database connection.
    """

    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 5432,
        statement_timeout_ms: int = 2000
    ) -> None:
        """Initialize DBManager with database connection parameters.
        
        Args:
            host: Database server hostname (e.g., 'localhost', 'db.example.com').
            database: Name of the database to connect to.
            user: Database username for authentication.
            password: Database password for authentication.
            port: Database server port. Defaults to 5432 (PostgreSQL default).
            statement_timeout_ms: Maximum query execution time in milliseconds.
                Defaults to 2000ms to prevent long-running queries.
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.statement_timeout_ms = statement_timeout_ms
        self.conn = self._create_connection()

    def _create_connection(self) -> connection:
        """Create and configure a new database connection.
        
        Constructs DSN from individual connection parameters and establishes
        a connection with autocommit enabled and timeout configured.
        
        Returns:
            Configured psycopg2 connection with autocommit and timeout set.
        """
        
        # TODO PART 2 : Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return None

    def get_all_games(self) -> list[Boardgame]:
        """Fetch all games from the database.
        
        Retrieves all games with basic information (no categories/designers).
        Games are ordered alphabetically by name. Use with caution on large
        databases as this may return thousands of games.
        
        Returns:
            List of all Boardgame objects ordered by name.
            Categories and designers lists will be empty.
            
        Example:
            >>> all_games = db.get_all_games()
            >>> print(f"Total games: {len(all_games)}")
            Total games: 15432
        """
        games = []
        #TODO Part 2:: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return games

    def get_games_by_name(self, name_query: str, limit: int = 10) -> list[Boardgame]:
        """Find games by name substring match (case-insensitive).
        
        Searches for games where the name contains the query string (case-insensitive).
        Results are ordered by popularity (number of votes descending).
        
        Args:
            name_query: Substring to search for in game names. Whitespace is stripped.
            limit: Maximum number of results to return. Defaults to 10.
            
        Returns:
            List of Boardgame objects matching the search, ordered by popularity.
            Returns basic game info only (no categories/designers populated).
            
        Example:
            >>> games = db.get_games_by_name("pandemic", limit=5)
            >>> for game in games:
            ...     print(f"{game.name}: {game.avgscore}/10")
            Pandemic: 7.8/10
            Pandemic Legacy: Season 1: 8.6/10
        """
        games = []
        #TODO Part 2: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return games
    

    
    def get_all_designers(self) -> list[Designer]:
        """Fetch all designers from the database.
        
        Retrieves all game designers with their IDs, names, and countries.
        Results are ordered alphabetically by designer name.
        
        Returns:
            List of all Designer objects ordered by name.
            
        Example:
            >>> designers = db.get_all_designers()
            >>> for d in designers[:3]:
            ...     print(f"{d.name} ({d.country})")
            Reiner Knizia (Germany)
            Matt Leacock (USA)
        """
        designers = []
        #TODO Part 2: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return designers
    
    def get_games_by_designer(self, designer_name: str) -> list[Boardgame]:
        """Find games by designer name substring match (case-insensitive).
        
        Searches for games by designers whose names contain the query string.
        Returns games with at least the matching designer populated in the
        designers list (may not include all designers for multi-designer games).
        
        Args:
            designer_name: Substring to search for in designer names.
                Whitespace is stripped and search is case-insensitive.
                
        Returns:
            List of Boardgame objects ordered by game name.
            Each game's designers list will contain at least the matching designer.
            
        Example:
            >>> games = db.get_games_by_designer("Knizia")
            >>> for game in games[:3]:
            ...     designer = game.designers[0]
            ...     print(f"{game.name} by {designer.name}")
            Ra by Reiner Knizia
            Tigris & Euphrates by Reiner Knizia
        """
        games = []
        #TODO Part 2: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return games

    def get_game_profile(self, g_id: int) -> Boardgame | None:
        """Get complete game profile with categories and designers."""
        boardgame_profile = None
        # TODO PART 3: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO
        return boardgame_profile

    @staticmethod
    def _constraint_clauses(c: Constraints) -> tuple[str, dict[str, Any]]:
        """Build WHERE clause and parameters from constraints.
        
        Helper method to convert Constraints object into SQL WHERE clause
        fragments and corresponding parameter dictionary for psycopg2.
        
        Args:
            c: Constraints object with filter criteria.
            
        Returns:
            Tuple of (where_clause_string, parameters_dict).
            WHERE clause uses named parameters (e.g., %(players)s).
        """
        where = ["1=1"]
        params: dict[str, Any] = {}
        if c.players is not None:
            where.append("g.minplayers <= %(players)s AND g.maxplayers >= %(players)s")
            params["players"] = c.players
        if c.minplayers is not None:
            where.append("g.maxplayers >= %(minplayers)s")
            params["minplayers"] = c.minplayers
        if c.maxplayers is not None:
            where.append("g.minplayers <= %(maxplayers)s")
            params["maxplayers"] = c.maxplayers
        if c.maxplaytime is not None:
            where.append("g.maxplaytime <= %(maxplaytime)s")
            params["maxplaytime"] = c.maxplaytime
        if c.minplaytime is not None:
            where.append("g.minplaytime >= %(minplaytime)s")
            params["minplaytime"] = c.minplaytime
        where.append("(g.numvotes IS NULL OR g.numvotes >= %(min_votes)s)")
        params["min_votes"] = c.min_votes
        return " AND ".join(where), params

    def search_categories(self, query: str | None = None, limit: int = 10) -> list[Category]:
        """Search for categories by name substring match.
        
        Args:
            query: Substring to search for in category names (case-insensitive).
                If None or empty, returns all categories.
            limit: Maximum number of results. Defaults to 10.
            
        Returns:
            List of Category objects matching the search.
            
        Example:
            >>> categories = db.search_categories("strategy")
            >>> all_cats = db.search_categories()  # Get all categories
        """
        # TODO PART 3: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO

    def search_designers(self, query: str | None = None, limit: int = 10) -> list[Designer]:
        """Search for designers by name substring match.
        
        Args:
            query: Substring to search for in designer names (case-insensitive).
                If None or empty, returns all designers.
            limit: Maximum number of results. Defaults to 10.
            
        Returns:
            List of Designer objects matching the search.
            
        Example:
            >>> designers = db.search_designers("knizia")
            >>> all_designers = db.search_designers()  # Get all designers
        """
        # TODO PART 3: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO

    def candidate_by_categories(
        self, 
        c_ids: list[int], 
        constraints: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Generate candidate games by category overlap.
        
        Finds games that share categories with a seed game, ranked by overlap count.
        Uses constraints to filter by player count, playtime, and rating quality.
        
        Args:
            c_ids: List of category IDs to match against.
            constraints: Dict of filter criteria (see Constraints class).
                Must include limit_candidates for result limit.
                
        Returns:
            List of dicts with {"g_id": int, "name": str, "cat_overlap": int}.
            Sorted by overlap descending, then by votes descending.
            Returns empty list if no categories specified.
            
        Example:
            >>> constraints = {"min_votes": 500, "limit_candidates": 50}
            >>> candidates = db.candidate_by_categories(c_ids=[1, 5, 10], constraints=constraints)
        """
        # TODO PART 3: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO

    def candidate_by_designers(self, des_ids: list[int], constraints: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Generate candidate games by designer overlap.
        
        Finds games that share designers with a seed game, ranked by overlap count.
        Uses constraints to filter by player count, playtime, and rating quality.
        
        Args:
            des_ids: List of designer IDs to match against.
            constraints: Dict of filter criteria (see Constraints class).
                
        Returns:
            List of dicts with {"g_id": int, "designer_overlap": int}.
            Sorted by overlap descending, then by votes descending.
            
        Example:
            >>> constraints = {"min_votes": 500, "limit_candidates": 50}
            >>> candidates = db.candidate_by_designers([42], constraints)
        """
        # TODO PART 3: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO

    def score_candidates(
        self, candidates: list[dict[str, Any]], constraints: dict[str, Any], exclude_g_ids: list[int]
    ) -> list[int]:
        """Score candidates and return top recommendations.
        
        Combines category and designer overlap signals with game quality metrics
        to produce a single score per game, then returns the highest-scoring games.
        
        Scoring formula:
            score = 0.55 * cat_overlap + 0.45 * designer_overlap + quality
            quality = avgscore + 0.15 * log10(numvotes + 1)
            
        Args:
            candidates: Combined output from candidate_by_categories and
                candidate_by_designers. Should have g_id and overlap fields.
            constraints: Dict must include limit_final (number of games to return).
            exclude_g_ids: Game IDs to exclude (e.g., seed game, already owned).
            
        Returns:
            List of game IDs for final recommendations, length <= limit_final.
            Ordered by score (highest to lowest).
            Returns empty list if no valid candidates.
            
        Example:
            >>> cat_cands = db.candidate_by_categories([1, 2], constraints)
            >>> des_cands = db.candidate_by_designers([5], constraints)
            >>> final_ids = db.score_candidates(
            ...     cat_cands + des_cands,
            ...     {"limit_final": 8},
            ...     [12345]
            ... )
            >>> len(final_ids)
            8
        """
        c = Constraints(**constraints)
        exclude = set(map(int, exclude_g_ids or []))

        # Combine overlaps for each game
        feats: dict[int, dict[str, float]] = {}
        for it in candidates:
            # Handle case where candidates is a list of integers instead of dicts
            if isinstance(it, int):
                gid = it
                if gid in exclude:
                    continue
                feats.setdefault(gid, {"cat_overlap": 0.0, "designer_overlap": 0.0})
            elif isinstance(it, dict):
                gid = int(it["g_id"])
                if gid in exclude:
                    continue
                d = feats.setdefault(gid, {"cat_overlap": 0.0, "designer_overlap": 0.0})
                if "cat_overlap" in it:
                    d["cat_overlap"] = max(d["cat_overlap"], float(it["cat_overlap"]))
                if "designer_overlap" in it:
                    d["designer_overlap"] = max(d["designer_overlap"], float(it["designer_overlap"]))
            else:
                # Skip invalid entries
                continue

        if not feats:
            return []

        gids = tuple(feats.keys())
        
        # Fetch game scores
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT g_id, avgscore, numvotes
                FROM games
                WHERE g_id IN %(gids)s;
                """,
                {"gids": gids},
            )
            stats = {
                int(r[0]): (float(r[1]) if r[1] is not None else 0.0, float(r[2]) if r[2] is not None else 0.0)
                for r in cur.fetchall()
            }

        # Score all candidates
        scored = []
        for gid, f in feats.items():
            avg, votes = stats.get(gid, (0.0, 0.0))
            quality = avg + 0.15 * math.log10(votes + 1.0)
            score = 0.55 * f["cat_overlap"] + 0.45 * f["designer_overlap"] + quality
            scored.append((gid, score))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[1], reverse=True)
        return [gid for gid, _ in scored[:c.limit_final]]


    def fetch_game_cards(self, g_ids: list[int]) -> list[Boardgame]:
        """Fetch complete game cards for a list of game IDs.
        
        Retrieves full game profiles by calling get_game_profile for each ID.
        
        Args:
            g_ids: List of game IDs to fetch. Order is preserved in results.
            
        Returns:
            List of Boardgame objects with full profiles (categories and designers).
            Games appear in same order as requested IDs.
            Missing IDs are silently skipped.
            
        Example:
            >>> cards = db.fetch_game_cards([1, 42, 100, 500])
            >>> for card in cards:
            ...     print(f"{card.name}: {len(card.categories)} categories")
            Catan: 3 categories
            Pandemic: 2 categories
        """
        if not g_ids:
            return []
        
        # Fetch each game profile individually
        games = []
        for g_id in g_ids:
            game = self.get_game_profile(g_id)
            if game:
                games.append(game)
        return games
    
    def close(self) -> None:
        """Close the persistent database connection.
        
        Should be called when done with the DBManager instance to free database
        resources. After calling close(), the DBManager instance should not be used.
        
        Example:
            >>> db = DBManager(host="localhost", database="boardgames",
            ...                user="user", password="pass")
            >>> games = db.find_games_by_name("catan")
            >>> db.close()  # Clean shutdown
        """
        # TODO PART 2: Complete this function
        raise NotImplementedError("TODO project sql") ### TODO


