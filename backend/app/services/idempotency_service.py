import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    idempotency_key: Mapped[str] = mapped_column(String(64), primary_key=True, index=True, nullable=False)
    response_status_code: Mapped[int] = mapped_column(nullable=False)
    response_body_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

async def check_idempotency_cache(
    session: AsyncSession,
    idempotency_key: str | None,
) -> tuple[bool, int | None, dict[str, Any] | None]:
    if not idempotency_key:
        return False, None, None
    stmt = select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        return True, record.response_status_code, json.loads(record.response_body_json)
    return False, None, None

async def save_idempotency_cache(
    session: AsyncSession,
    idempotency_key: str | None,
    status_code: int,
    response_body: dict[str, Any],
) -> None:
    if not idempotency_key:
        return
    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        response_status_code=status_code,
        response_body_json=json.dumps(response_body, default=str),
    )
    session.add(record)
    await session.flush()

