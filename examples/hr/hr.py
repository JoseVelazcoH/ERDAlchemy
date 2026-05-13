"""HR schema — 1:1 relationships alongside 1:N."""

from sqlalchemy import ForeignKey, String, Text, Date, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date
from decimal import Decimal


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    budget: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department", foreign_keys="Employee.department_id"
    )
    manager: Mapped["Employee | None"] = relationship(
        back_populates="managed_department", foreign_keys="Employee.manages_department_id"
    )


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    manages_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String(200))
    position: Mapped[str] = mapped_column(String(100))
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    hire_date: Mapped[date] = mapped_column(Date)
    department: Mapped["Department"] = relationship(
        back_populates="employees", foreign_keys=[department_id]
    )
    managed_department: Mapped["Department | None"] = relationship(
        back_populates="manager", foreign_keys=[manages_department_id]
    )
    profile: Mapped["EmployeeProfile | None"] = relationship(back_populates="employee")


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    emergency_contact: Mapped[str | None] = mapped_column(String(200))
    employee: Mapped["Employee"] = relationship(back_populates="profile")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))


if __name__ == "__main__":
    from sqlalchemy_erd import generate_erd

    generate_erd(
        Base,
        output="examples/hr/hr.png",
        format="png",
        theme="green",
        title="HR (1:1, 1:N)",
        scale=2,
        table_colors={"employee_profiles": "#1e40af"},
    )
    print("Generated examples/hr/hr.png")
