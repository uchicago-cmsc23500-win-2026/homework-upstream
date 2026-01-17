import pytest
import os

from db import DBManager, Boardgame, Designer


# Set up pytest fixture for database connection
@pytest.fixture
def db_connection():
    return DBManager(host="wellington.cs.uchicago.edu",
        database="boardgames",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )

def test_get_all_games(db_connection):
    games = db_connection.get_all_games()
    assert len(games) == 219
    assert all([isinstance(game, Boardgame) for game in games])


def test_get_all_designers(db_connection):
    designers = db_connection.get_all_designers()
    assert len(designers) == 28
    assert all([isinstance(designer, Designer) for designer in designers])


@pytest.mark.parametrize("name,expected",
     [("game", 26), ("monopoly", 21), ("risk", 7), ("clue", 7) ])
def test_get_games_by_name(db_connection, name, expected):
    games = db_connection.get_games_by_name(name, limit=100)
    assert all([isinstance(game, Boardgame) for game in games])
    assert len(games) == expected
    assert all([type(game.name) == str for game in games])
    assert all([name in game.name.lower() for game in games])


@pytest.mark.parametrize("name,expected",
     [("rob", 26), ("david", 3), ("matt", 5), ("maggi", 7) ])
def test_get_games_by_designer(db_connection, name, expected):
    games = db_connection.get_games_by_designer(name)
    assert all([isinstance(game, Boardgame) for game in games])
    assert len(games) == expected
    assert all([len(game.designers) > 0 for game in games])
    assert all([name in game.designers[0].name.lower() for game in games])
