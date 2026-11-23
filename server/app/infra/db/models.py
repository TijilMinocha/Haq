from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, datetime: DateTime(timezone=True)}


class OperatorRow(Base):
    __tablename__ = "operators"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CaseRow(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    mode: Mapped[str] = mapped_column(String(16))
    language: Mapped[str] = mapped_column(String(8))
    subject: Mapped[dict[str, Any]]
    event: Mapped[dict[str, Any]]
    nominee: Mapped[dict[str, Any]]
    pin_hash: Mapped[str] = mapped_column(String(255))
    owner_operator_id: Mapped[str | None] = mapped_column(
        ForeignKey("operators.id", ondelete="SET NULL"), index=True
    )
    scenario_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime]

    documents: Mapped[list["DocumentRow"]] = relationship(
        back_populates="case",
        order_by="DocumentRow.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tokens: Mapped[list["CaseTokenRow"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class CaseTokenRow(Base):
    __tablename__ = "case_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DocumentRow(Base):
    """Extracted fields only. The uploaded image is never stored."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    fields: Mapped[dict[str, Any]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    case: Mapped[CaseRow] = relationship(back_populates="documents")


class AuthFailureRow(Base):
    """Failed PIN or password attempts, kept in the database so lockout survives restarts
    and holds across server instances."""

    __tablename__ = "auth_failures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(254), index=True)
    failed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
