"""Showcase schema for the layered layout: many tables, several FK levels, wide cards.

Run from the repository root:

    python examples/showcase/showcase.py
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_erd import generate_erd


class Base(DeclarativeBase):
    pass


# ── Catalogs (layer 0) ──
class Country(Base):
    __tablename__ = "countries"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(100))


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100))


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))


class LoyaltyTier(Base):
    __tablename__ = "loyalty_tiers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    min_points: Mapped[int] = mapped_column(Integer)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2))


# ── Entities depending on catalogs (layer 1) ──
class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(40))
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    loyalty_tier_id: Mapped[int] = mapped_column(ForeignKey("loyalty_tiers.id"))
    address_line1: Mapped[str] = mapped_column(String(200))
    address_line2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    stock_qty: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    title: Mapped[str] = mapped_column(String(100))
    hired_at: Mapped[datetime] = mapped_column(DateTime)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean)


# ── Transactions (layer 2) ──
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[str] = mapped_column(String(50))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime)


# ── Line items (layer 3) ──
class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2))


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    carrier: Mapped[str] = mapped_column(String(100))
    tracking_number: Mapped[str] = mapped_column(String(100))
    shipped_at: Mapped[datetime] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)


if __name__ == "__main__":
    generate_erd(
        Base,
        output="examples/showcase/showcase.png",
        format="png",
        title="Showcase (layered)",
        scale=2,
    )
