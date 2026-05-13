"""Demo: Generate ERD from sample SQLAlchemy 2.0 models."""

from sqlalchemy import ForeignKey, String, Text, JSON, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date


class Base(DeclarativeBase):
    pass


class Proyecto(Base):
    __tablename__ = "proyectos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    productos: Mapped[list["Producto"]] = relationship(back_populates="proyecto")


class Producto(Base):
    __tablename__ = "productos"
    id: Mapped[int] = mapped_column(primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(ForeignKey("proyectos.id"))
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    proyecto: Mapped["Proyecto"] = relationship(back_populates="productos")


class BaseDeDatos(Base):
    __tablename__ = "bases_de_datos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    tema: Mapped[str | None] = mapped_column(Text)
    frecuencia_actualizacion: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    tablas: Mapped[list["Tabla"]] = relationship(back_populates="base_de_datos")
    instrumentos: Mapped[list["Instrumento"]] = relationship(back_populates="base_de_datos")


class Tabla(Base):
    __tablename__ = "tablas"
    id: Mapped[int] = mapped_column(primary_key=True)
    base_de_datos_id: Mapped[int] = mapped_column(ForeignKey("bases_de_datos.id"))
    nombre: Mapped[str] = mapped_column(String(200))
    campos: Mapped[dict | None] = mapped_column(JSON)
    meta: Mapped[dict | None] = mapped_column(JSON)
    base_de_datos: Mapped["BaseDeDatos"] = relationship(back_populates="tablas")


class Instrumento(Base):
    __tablename__ = "instrumentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    base_de_datos_id: Mapped[int] = mapped_column(ForeignKey("bases_de_datos.id"))
    nombre: Mapped[str] = mapped_column(String(200))
    fecha_publicacion: Mapped[date | None] = mapped_column(Date)
    descripcion: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    base_de_datos: Mapped["BaseDeDatos"] = relationship(back_populates="instrumentos")
    urls: Mapped[list["Url"]] = relationship(back_populates="instrumento")


class Url(Base):
    __tablename__ = "urls"
    id: Mapped[int] = mapped_column(primary_key=True)
    instrumento_id: Mapped[int] = mapped_column(ForeignKey("instrumentos.id"))
    url: Mapped[str] = mapped_column(String(500))
    meta: Mapped[dict | None] = mapped_column(JSON)
    instrumento: Mapped["Instrumento"] = relationship(back_populates="urls")
    archivos: Mapped[list["Archivo"]] = relationship(back_populates="url")


class Archivo(Base):
    __tablename__ = "archivos"
    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("urls.id"))
    descripcion: Mapped[str | None] = mapped_column(Text)
    fecha_fuente: Mapped[date | None] = mapped_column(Date)
    fecha_publicacion: Mapped[date | None] = mapped_column(Date)
    meta: Mapped[dict | None] = mapped_column(JSON)
    url: Mapped["Url"] = relationship(back_populates="archivos")


if __name__ == "__main__":
    from sqlalchemy_erd import generate_erd

    generate_erd(
        Base,
        output="erd.html",
        format="html",
        theme="default",
        title="Dashboard Tracking ERD",
        table_colors={
            "urls": "#1e40af",
            "archivos": "#065f46",
        },
    )
    print("Generated erd.html — open in browser")
