"""University schema — N:N relationships via association tables."""

from sqlalchemy import ForeignKey, String, Text, Date, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date


class Base(DeclarativeBase):
    pass


enrollment = Table(
    "enrollments",
    Base.metadata,
    Column("student_id", ForeignKey("students.id"), primary_key=True),
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
)

teaching = Table(
    "teaching",
    Base.metadata,
    Column("professor_id", ForeignKey("professors.id"), primary_key=True),
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    building: Mapped[str | None] = mapped_column(String(100))
    courses: Mapped[list["Course"]] = relationship(back_populates="department")
    professors: Mapped[list["Professor"]] = relationship(back_populates="department")


class Professor(Base):
    __tablename__ = "professors"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    department: Mapped["Department"] = relationship(back_populates="professors")
    courses: Mapped[list["Course"]] = relationship(secondary=teaching, back_populates="professors")


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    department: Mapped["Department"] = relationship(back_populates="courses")
    students: Mapped[list["Student"]] = relationship(secondary=enrollment, back_populates="courses")
    professors: Mapped[list["Professor"]] = relationship(secondary=teaching, back_populates="courses")


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    enrollment_date: Mapped[date] = mapped_column(Date)
    courses: Mapped[list["Course"]] = relationship(secondary=enrollment, back_populates="students")


if __name__ == "__main__":
    from sqlalchemy_erd import generate_erd

    generate_erd(
        Base,
        output="examples/university/university.png",
        format="png",
        theme="blue",
        title="University (N:N)",
        scale=2,
    )
    print("Generated examples/university/university.png")
