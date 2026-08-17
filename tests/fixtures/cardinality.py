"""Fixtures for relationship cardinality schemas."""

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, Text


# -- Cardinality schema -------------------------------------------------------

cardinality_metadata = MetaData()

Table(
    "users", cardinality_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
)

Table(
    "profiles", cardinality_metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("bio", Text),
)

Table(
    "avatars", cardinality_metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), unique=True, nullable=False),
)

Table(
    "tasks", cardinality_metadata,
    Column("id", Integer, primary_key=True),
    Column("assignee_id", Integer, ForeignKey("users.id"), nullable=True),
)


@pytest.fixture
def cardinality_metadata_fixture():
    return cardinality_metadata
