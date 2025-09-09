from __future__ import annotations

import uuid

from sqlalchemy import Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP


class UUIDPKMixin:
    """UUID первичный ключ."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, doc="PK UUID"
    )


class TimestampMixin:
    """created_at / updated_at (TIMESTAMPTZ). Для «обычных» таблиц."""
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(),
        doc="Когда запись создана"
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
        doc="Когда запись послед раз обновлялась"
    )


class CreatedAtMixin:
    """Только created_at — пригодно для журналов (append-only)."""
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(),
        doc="Время создания события/журнальной записи"
    )


class IsActiveMixin:
    """Флаг активности записи."""
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), doc="Активна ли запись"
    )


class SoftDeleteMixin:
    """Мягкое удаление через флаг (опционально)."""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        doc="Пометка об удалении"
    )
