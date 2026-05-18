"""Multi-schema — tables across public, billing, and audit schemas."""

from sqlalchemy import ForeignKey, String, Text, DateTime, Numeric, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "public"}
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Numeric(10, 2))


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "billing"}
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("public.users.id"))
    total: Mapped[float] = mapped_column(Numeric(10, 2))
    issued_at: Mapped[datetime] = mapped_column(DateTime)


class LineItem(Base):
    __tablename__ = "line_items"
    __table_args__ = {"schema": "billing"}
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("billing.invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("public.products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "audit"}
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("public.users.id"))
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


if __name__ == "__main__":
    from sqlalchemy_erd import generate_erd

    generate_erd(
        Base,
        output="examples/multi_schema/multi_schema.html",
        format="html",
        title="Multi-Schema ERD",
    )
    generate_erd(
        Base,
        output="examples/multi_schema/multi_schema.png",
        format="png",
        title="Multi-Schema ERD",
        scale=1,
    )
    print("Generated examples/multi_schema/multi_schema.html")
    print("Generated examples/multi_schema/multi_schema.png")
