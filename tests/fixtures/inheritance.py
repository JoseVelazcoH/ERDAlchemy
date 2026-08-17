"""Fixtures for SQLAlchemy inheritance schemas."""

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# -- Joined-table inheritance schema -----------------------------------------

class InheritanceBase(DeclarativeBase):
    pass


class Employee(InheritanceBase):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_identity": "employee",
    }


class Manager(Employee):
    __tablename__ = "managers"
    id: Mapped[int] = mapped_column(ForeignKey("employees.id"), primary_key=True)
    department: Mapped[str] = mapped_column(String(100))
    __mapper_args__ = {"polymorphic_identity": "manager"}


@pytest.fixture
def inheritance_base():
    return InheritanceBase


# -- Inheritance plus an extra FK to the same parent --------------------------

class InheritanceExtraFkBase(DeclarativeBase):
    pass


class Staff(InheritanceExtraFkBase):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(50))
    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_identity": "staff",
    }


class Lead(Staff):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(ForeignKey("staff.id"), primary_key=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    __mapper_args__ = {
        "polymorphic_identity": "lead",
        "inherit_condition": id == Staff.id,
    }


@pytest.fixture
def inheritance_extra_fk_base():
    return InheritanceExtraFkBase

