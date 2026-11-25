# Configuration commune aux tests : base SQLite temporaire à la place de PostgreSQL
# (les tests ne touchent jamais la vraie base et tournent sans serveur PostgreSQL)

import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")

import pytest  # noqa: E402

from app.database import Base, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def creer_tables():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)