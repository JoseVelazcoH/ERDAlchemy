"""Shared fixtures for the ERDAlchemy test suite."""

from __future__ import annotations

import pytest
from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, DateTime, Boolean,
    Float, Numeric, JSON, BigInteger, SmallInteger, Date, Uuid,
    Table, MetaData,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal


# ── Single-table schema ──────────────────────────────────────────────────────

class SingleBase(DeclarativeBase):
    pass


class Standalone(SingleBase):
    __tablename__ = "standalone"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


@pytest.fixture
def single_table_base():
    return SingleBase


# ── Blog schema (1:N) ────────────────────────────────────────────────────────

class BlogBase(DeclarativeBase):
    pass


class User(BlogBase):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")


class Post(BlogBase):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    author: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")


class Comment(BlogBase):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


@pytest.fixture
def blog_base():
    return BlogBase


# ── Many-to-many schema (association table) ──────────────────────────────────

class M2MBase(DeclarativeBase):
    pass


student_course = Table(
    "student_courses",
    M2MBase.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
)


class Student(M2MBase):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    courses: Mapped[list["Course"]] = relationship(
        secondary=student_course, back_populates="students",
    )


class Course(M2MBase):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    students: Mapped[list["Student"]] = relationship(
        secondary=student_course, back_populates="courses",
    )


@pytest.fixture
def m2m_base():
    return M2MBase


# ── Empty schema ─────────────────────────────────────────────────────────────

class EmptyBase(DeclarativeBase):
    pass


@pytest.fixture
def empty_base():
    return EmptyBase


# ── Circular FK schema ───────────────────────────────────────────────────────

circular_metadata = MetaData()

Table(
    "departments", circular_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("manager_id", Integer, ForeignKey("employees.id")),
)

Table(
    "employees", circular_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("department_id", Integer, ForeignKey("departments.id")),
)


@pytest.fixture
def circular_metadata_fixture():
    return circular_metadata


# ── All column types schema ──────────────────────────────────────────────────

class TypesBase(DeclarativeBase):
    pass


class AllTypes(TypesBase):
    __tablename__ = "all_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    big: Mapped[int] = mapped_column(BigInteger)
    small: Mapped[int] = mapped_column(SmallInteger)
    floating: Mapped[float] = mapped_column(Float)
    decimal_col: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    text_col: Mapped[str] = mapped_column(Text)
    string_col: Mapped[str] = mapped_column(String(50))
    date_col: Mapped[datetime] = mapped_column(Date)
    datetime_col: Mapped[datetime] = mapped_column(DateTime)
    bool_col: Mapped[bool] = mapped_column(Boolean)
    json_col: Mapped[dict | None] = mapped_column(JSON, nullable=True)


@pytest.fixture
def types_base():
    return TypesBase


# ── Multi-schema (cross-schema FKs) ─────────────────────────────────────────

multi_schema_metadata = MetaData()

Table(
    "accounts", multi_schema_metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(200)),
    schema="auth",
)

Table(
    "orders", multi_schema_metadata,
    Column("id", Integer, primary_key=True),
    Column("account_id", Integer, ForeignKey("auth.accounts.id")),
    Column("total", Numeric(10, 2)),
    schema="billing",
)


@pytest.fixture
def multi_schema_metadata_fixture():
    return multi_schema_metadata
