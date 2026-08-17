"""Fixtures for schemas carrying column comments."""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table

comments_metadata = MetaData()

Table(
    "accounts", comments_metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(200), comment="Primary login email"),
)


@pytest.fixture
def comments_metadata_fixture():
    return comments_metadata
