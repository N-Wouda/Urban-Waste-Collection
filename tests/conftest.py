import pytest

from waste.classes import Database


@pytest.fixture(scope="function")
def test_db():
    return Database("tests/test.db", ":memory:")
