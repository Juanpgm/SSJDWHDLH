import os
import sys
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.main import app  # noqa: E402


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/railway_test",
    )


@pytest.fixture(scope="session")
def client(database_url: str) -> Generator[TestClient, Any, None]:
    os.environ["DATABASE_URL"] = database_url
    with TestClient(app) as c:
        yield c
