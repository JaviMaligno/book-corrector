from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine


def _build_engine():
    url = os.environ.get("DATABASE_URL", "sqlite:///./local.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=False, connect_args=connect_args)


engine = _build_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
